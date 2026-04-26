from __future__ import annotations

import json
import logging
import re

from bs4 import BeautifulSoup

from models import Listing, SearchParams, Source
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

MAKE_SLUG = {
    "rivian": "rivian",
    "tesla": "tesla",
    "ford": "ford",
    "chevrolet": "chevrolet",
    "bmw": "bmw",
    "mercedes-benz": "mercedes_benz",
}

MODEL_SLUG = {
    "r1s": "rivian-r1s",
    "r1t": "rivian-r1t",
    "model_y": "tesla-model_y",
    "model_3": "tesla-model_3",
    "f-150_lightning": "ford-f_150_lightning",
}


class CarsComScraper(BaseScraper):
    source = Source.CARS_COM
    base_url = "https://www.cars.com"

    async def search(self, params: SearchParams) -> list[Listing]:
        try:
            make_slug = MAKE_SLUG.get(params.make.lower(), params.make.lower())
            model_key = params.model.lower().replace(" ", "_")
            model_slug = MODEL_SLUG.get(model_key, f"{make_slug}-{model_key}")

            url = f"{self.base_url}/shopping/results/"
            query_params = {
                "stock_type": params.condition if params.condition != "all" else "all",
                "makes[]": make_slug,
                "models[]": model_slug,
                "zip": params.zip_code,
                "maximum_distance": str(params.radius_miles),
                "page_size": "50",
            }
            if params.year_min:
                query_params["year_min"] = str(params.year_min)
            if params.year_max:
                query_params["year_max"] = str(params.year_max)
            if params.price_min:
                query_params["list_price_min"] = str(params.price_min)
            if params.price_max:
                query_params["list_price_max"] = str(params.price_max)
            if params.mileage_max:
                query_params["mileage_max"] = str(params.mileage_max)

            resp = await self._get(url, params=query_params)
            return self._parse(resp.text, params)

        except Exception:
            logger.exception("Cars.com scrape failed")
            return []

    def _parse(self, html: str, params: SearchParams) -> list[Listing]:
        listings: list[Listing] = []
        soup = BeautifulSoup(html, "lxml")

        # Try JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") in ("Car", "Vehicle", "Product"):
                            listing = self._from_jsonld(item, params)
                            if listing:
                                listings.append(listing)
                elif isinstance(data, dict):
                    if data.get("@type") == "ItemList":
                        for el in data.get("itemListElement", []):
                            item = el.get("item", el)
                            listing = self._from_jsonld(item, params)
                            if listing:
                                listings.append(listing)
            except (json.JSONDecodeError, KeyError):
                continue

        if listings:
            return listings

        # HTML card parsing
        cards = soup.select(".vehicle-card, [data-testid='vehicle-card'], .shop-srp-listings__listing")
        for card in cards:
            listing = self._parse_card(card, params)
            if listing:
                listings.append(listing)

        return listings

    def _from_jsonld(self, item: dict, params: SearchParams) -> Listing | None:
        try:
            offers = item.get("offers", {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            price = int(float(str(offers.get("price", "0")).replace(",", "").replace("$", "")))
            if price <= 0:
                return None

            name = item.get("name", "")
            year = int(item.get("vehicleModelDate", item.get("modelDate", 0)))
            mileage_raw = item.get("mileageFromOdometer", {})
            if isinstance(mileage_raw, dict):
                mileage = int(float(str(mileage_raw.get("value", "0")).replace(",", "")))
            else:
                mileage = int(float(str(mileage_raw).replace(",", ""))) if mileage_raw else 0

            url = item.get("url", "")
            if url and not url.startswith("http"):
                url = f"{self.base_url}{url}"

            return Listing(
                id=self._make_id("carscom", name, str(price)),
                source=self.source,
                title=name,
                year=year,
                make=params.make,
                model=params.model,
                trim=item.get("vehicleConfiguration", ""),
                price=price,
                mileage=mileage,
                exterior_color=item.get("color", ""),
                vin=item.get("vehicleIdentificationNumber", ""),
                listing_url=url,
                image_url=item.get("image", ""),
                dealer_name=offers.get("seller", {}).get("name", "") if isinstance(offers.get("seller"), dict) else "",
            )
        except (ValueError, TypeError):
            return None

    def _parse_card(self, card: object, params: SearchParams) -> Listing | None:
        try:
            title_el = card.select_one(".title, h2, [data-testid='vehicle-card-title']")
            price_el = card.select_one(".primary-price, [data-testid='vehicle-card-price']")
            mileage_el = card.select_one(".mileage, [data-testid='vehicle-card-mileage']")
            dealer_el = card.select_one(".dealer-name")
            img_el = card.select_one("img")
            link_el = card.select_one("a[href*='/vehicledetail/']")

            title = title_el.get_text(strip=True) if title_el else ""
            price_text = price_el.get_text(strip=True) if price_el else "0"
            price = int(re.sub(r"[^\d]", "", price_text) or 0)
            if price <= 0:
                return None

            mileage_text = mileage_el.get_text(strip=True) if mileage_el else "0"
            mileage = int(re.sub(r"[^\d]", "", mileage_text) or 0)

            year_match = re.match(r"(\d{4})", title)
            year = int(year_match.group(1)) if year_match else 2024

            href = ""
            if link_el:
                href = link_el.get("href", "")
                if href and not href.startswith("http"):
                    href = f"{self.base_url}{href}"

            return Listing(
                id=self._make_id("carscom", title, str(price)),
                source=self.source,
                title=title,
                year=year,
                make=params.make,
                model=params.model,
                price=price,
                mileage=mileage,
                dealer_name=dealer_el.get_text(strip=True) if dealer_el else "",
                image_url=img_el.get("src", "") if img_el else "",
                listing_url=href,
            )
        except (ValueError, TypeError, AttributeError):
            return None
