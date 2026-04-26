from __future__ import annotations

import json
import logging
import re

from bs4 import BeautifulSoup

from models import Listing, SearchParams, Source
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CarvanaScraper(BaseScraper):
    source = Source.CARVANA
    base_url = "https://www.carvana.com"

    async def search(self, params: SearchParams) -> list[Listing]:
        try:
            make = params.make.lower()
            model = params.model.lower().replace(" ", "-")
            url = f"{self.base_url}/cars/{make}-{model}"

            query_params: dict[str, str] = {}
            if params.price_max:
                query_params["price-max"] = str(params.price_max)
            if params.price_min:
                query_params["price-min"] = str(params.price_min)
            if params.mileage_max:
                query_params["mileage-max"] = str(params.mileage_max)
            if params.year_min:
                query_params["year-min"] = str(params.year_min)
            if params.year_max:
                query_params["year-max"] = str(params.year_max)

            resp = await self._get(url, params=query_params)
            return self._parse(resp.text, params)

        except Exception:
            logger.exception("Carvana scrape failed")
            return []

    def _parse(self, html: str, params: SearchParams) -> list[Listing]:
        listings: list[Listing] = []
        soup = BeautifulSoup(html, "lxml")

        # Carvana uses Next.js — try __NEXT_DATA__
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                data = json.loads(script.string)
                page_props = data.get("props", {}).get("pageProps", {})
                vehicles = (
                    page_props.get("inventory", {}).get("vehicles", [])
                    or page_props.get("vehicles", [])
                    or page_props.get("results", [])
                )
                for v in vehicles[:50]:
                    listing = self._parse_vehicle(v, params)
                    if listing:
                        listings.append(listing)
            except (json.JSONDecodeError, KeyError):
                pass

        if listings:
            return listings

        # Try embedded JSON state
        pattern = r'window\.__(?:PRELOADED_STATE|INITIAL_STATE)__\s*=\s*({.*?});?\s*</script>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                state = json.loads(match.group(1))
                vehicles = (
                    state.get("inventory", {}).get("vehicles", [])
                    or state.get("vehicles", [])
                )
                for v in vehicles[:50]:
                    listing = self._parse_vehicle(v, params)
                    if listing:
                        listings.append(listing)
            except (json.JSONDecodeError, KeyError):
                pass

        if listings:
            return listings

        # HTML fallback
        cards = soup.select("[data-test='ResultTile'], .result-tile, .vehicle-card")
        for card in cards:
            listing = self._parse_card(card, params)
            if listing:
                listings.append(listing)

        return listings

    def _parse_vehicle(self, v: dict, params: SearchParams) -> Listing | None:
        try:
            price = int(v.get("price", 0) or v.get("basePrice", 0))
            if price <= 0:
                return None

            year = int(v.get("year", 2024))
            mileage = int(v.get("mileage", 0))
            make = v.get("make", params.make)
            model = v.get("model", params.model)
            trim = v.get("trim", "")

            title = f"{year} {make} {model}"
            if trim:
                title += f" {trim}"

            stock_no = v.get("stockNumber", v.get("id", ""))
            listing_url = f"{self.base_url}/vehicle/{stock_no}" if stock_no else ""

            images = v.get("images", v.get("mediumImages", []))
            image_url = ""
            if isinstance(images, list) and images:
                image_url = images[0] if isinstance(images[0], str) else images[0].get("url", "")
            elif isinstance(images, str):
                image_url = images

            return Listing(
                id=self._make_id("carvana", str(stock_no), str(price)),
                source=self.source,
                title=title,
                year=year,
                make=make,
                model=model,
                trim=trim,
                price=price,
                mileage=mileage,
                exterior_color=v.get("exteriorColor", ""),
                interior_color=v.get("interiorColor", ""),
                vin=v.get("vin", ""),
                dealer_name="Carvana",
                listing_url=listing_url,
                image_url=image_url,
                condition="Used",
            )
        except (ValueError, TypeError):
            return None

    def _parse_card(self, card: object, params: SearchParams) -> Listing | None:
        try:
            title_el = card.select_one("[data-test='TileTitle'], .vehicle-title, h3")
            price_el = card.select_one("[data-test='TilePrice'], .vehicle-price")
            mileage_el = card.select_one("[data-test='TileMileage'], .vehicle-mileage")
            img_el = card.select_one("img")
            link_el = card.select_one("a[href]")

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
                id=self._make_id("carvana", title, str(price)),
                source=self.source,
                title=title,
                year=year,
                make=params.make,
                model=params.model,
                price=price,
                mileage=mileage,
                dealer_name="Carvana",
                image_url=img_el.get("src", "") if img_el else "",
                listing_url=href,
                condition="Used",
            )
        except (ValueError, TypeError, AttributeError):
            return None
