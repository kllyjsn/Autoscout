from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from analytics import compute_analytics
from models import Listing, SearchParams, SearchResponse, Source
from scoring import score_listings
from scrapers import ALL_SCRAPERS

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AutoScout API",
    description="Car market aggregator — real-time listings from CarGurus, Cars.com, AutoTrader, Carvana, CarMax",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_PATH = os.path.join(os.path.dirname(__file__), "scraped_data.json")


def _load_cached_listings(params: SearchParams) -> list[Listing]:
    """Load pre-scraped listings from JSON cache as fallback."""
    if not os.path.exists(CACHE_PATH):
        return []
    try:
        with open(CACHE_PATH) as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    listings: list[Listing] = []
    for item in raw:
        # Filter by make/model if not matching
        item_make = item.get("make", "").lower()
        item_model = item.get("model", "").lower()
        if params.make.lower() != item_make or params.model.lower() != item_model:
            continue

        price = item.get("price", 0)
        mileage = item.get("mileage", 0)

        # AutoTrader mileage fix: values < 200 are in thousands
        if item.get("source") == "AutoTrader" and 0 < mileage < 200:
            mileage *= 1000

        # Apply filters
        if params.price_min and price < params.price_min:
            continue
        if params.price_max and price > params.price_max:
            continue
        if params.mileage_max and mileage > params.mileage_max:
            continue
        if params.year_min and item.get("year", 0) < params.year_min:
            continue
        if params.year_max and item.get("year", 9999) > params.year_max:
            continue

        try:
            source = Source(item.get("source", "AutoTrader"))
        except ValueError:
            continue

        listings.append(Listing(
            id=item.get("id", ""),
            source=source,
            title=item.get("title", ""),
            year=item.get("year", 2024),
            make=item.get("make", params.make),
            model=item.get("model", params.model),
            trim=item.get("trim", ""),
            price=price,
            mileage=mileage,
            exterior_color=item.get("exterior_color", ""),
            interior_color=item.get("interior_color", ""),
            vin=item.get("vin", ""),
            dealer_name=item.get("dealer_name", ""),
            location=item.get("location", ""),
            image_url=item.get("image_url", ""),
            listing_url=item.get("listing_url", ""),
            days_on_market=item.get("days_on_market"),
            condition=item.get("condition", "Used"),
            fuel_type=item.get("fuel_type", "Electric"),
        ))
    return listings


@app.get("/")
async def root():
    return {
        "service": "AutoScout API",
        "version": "0.1.0",
        "endpoints": {
            "search": "/api/search",
            "health": "/api/health",
        },
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}


@app.get("/api/search", response_model=SearchResponse)
async def search(
    make: str = "Rivian",
    model: str = "R1S",
    zip_code: str = "10001",
    radius_miles: int = 500,
    year_min: int | None = None,
    year_max: int | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    mileage_max: int | None = None,
    condition: str = "all",
):
    params = SearchParams(
        make=make,
        model=model,
        zip_code=zip_code,
        radius_miles=radius_miles,
        year_min=year_min,
        year_max=year_max,
        price_min=price_min,
        price_max=price_max,
        mileage_max=mileage_max,
        condition=condition,
    )

    scrapers = [cls() for cls in ALL_SCRAPERS]
    sources_queried = [s.source.value for s in scrapers]
    sources_succeeded: list[str] = []
    sources_failed: list[str] = []

    # Run all scrapers concurrently
    tasks = [_run_scraper(s, params) for s in scrapers]
    results = await asyncio.gather(*tasks)

    all_listings: list[Listing] = []
    for scraper, listings in zip(scrapers, results):
        if listings:
            all_listings.extend(listings)
            sources_succeeded.append(scraper.source.value)
            logger.info(f"{scraper.source.value}: {len(listings)} listings (live)")
        else:
            sources_failed.append(scraper.source.value)

    # If live scraping got few results, supplement with cached data
    live_count = len(all_listings)
    if live_count < 10:
        cached = _load_cached_listings(params)
        if cached:
            # Merge cached listings (avoid duplicates by title+price)
            existing = {(l.title, l.price) for l in all_listings}
            for cl in cached:
                if (cl.title, cl.price) not in existing:
                    all_listings.append(cl)
                    existing.add((cl.title, cl.price))

            # Update source tracking for cached data
            cached_sources = {l.source.value for l in cached}
            for cs in cached_sources:
                if cs in sources_failed:
                    sources_failed.remove(cs)
                if cs not in sources_succeeded:
                    sources_succeeded.append(cs)

            logger.info(f"Added {len(all_listings) - live_count} cached listings")

    # Score and analyze
    all_listings = score_listings(all_listings)
    all_listings.sort(key=lambda l: l.deal_score, reverse=True)
    analytics = compute_analytics(all_listings)

    return SearchResponse(
        listings=all_listings,
        analytics=analytics,
        query=params,
        sources_queried=sources_queried,
        sources_succeeded=sources_succeeded,
        sources_failed=sources_failed,
    )


async def _run_scraper(scraper, params: SearchParams):
    try:
        return await asyncio.wait_for(scraper.search(params), timeout=25.0)
    except asyncio.TimeoutError:
        logger.warning(f"{scraper.source.value}: timeout")
        return None
    except Exception:
        logger.exception(f"{scraper.source.value}: error")
        return None
