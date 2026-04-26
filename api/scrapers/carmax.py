from __future__ import annotations

import json
import logging
import re

from bs4 import BeautifulSoup

from models import Listing, SearchParams, Source
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CarMaxScraper(BaseScraper):
    source = Source.CARMAX
    base_url = "https://www.carmax.com"

    async def search(self, params: SearchParams) -> list[Listing]:
        try:
            make = params.make.lower()
            model = params.model.lower().replace(" ", "-")

            # CarMax search API
            url = f"{self.base_url}/cars/{make}/{model}"
            resp = await self._get(url)
            return self._parse(resp.text, params)

        except Exception:
            logger.exception("CarMax scrape failed")
            return []

    def _parse(self, html: str, params: SearchParams) -> list[Listing]:
        listings: list[Listing] = []
        soup = BeautifulSoup(html, "lxml")

        # CarMax uses Next.js
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                data = json.loads(script.string)
                page_props = data.get("props", {}).get("pageProps", {})
                items = (
                    page_props.get("cars", [])
                    or page_props.get("vehicles", [])
                    or page_props.get("searchResults", {}).get("items", [])
                )
                for item in items[:50]:
                    listing = self._parse_item(item, params)
                    if listing:
                        listings.append(listing)
            except (json.JSONDecodeError, KeyError):
                pass

        if listings:
            return listings

        # Try embedded data
        pattern = r'window\.__(?:PRELOADED_STATE|INITIAL_STATE|APP_STATE)__\s*=\s*({.*?});?\s*</script>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                state = json.loads(match.group(1))
                items = state.get("search", {}).get("results", [])
                for item in items[:50]:
                    listing = self._parse_item(item, params)
                    if listing:
                        listings.append(listing)
            except (json.JSONDecodeError, KeyError):
                pass

        if listings:
            return listings

        # HTML fallback
        cards = soup.select("[data-testid='car-tile'], .car-tile, .result-card")
        for card in cards:
            listing = self._parse_card(card, params)
            if listing:
                listings.append(listing)

        return listings

    def _parse_item(self, item: dict, params: SearchParams) -> Listing | None:
        try:
            price = int(item.get("price", 0) or item.get("basePrice", 0))
            if price <= 0:
                return None

            year = int(item.get("year", 2024))
            make = item.get("make", params.make)
            model = item.get("model", params.model)
            trim = item.get("trim", "")

            title = f"{year} {make} {model}"
            if trim:
                title += f" {trim}"

            stock_no = item.get("stockNumber", item.get("id", ""))
            listing_url = f"{self.base_url}/car/{stock_no}" if stock_no else ""

            images = item.get("images", item.get("photoUrls", []))
            image_url = ""
            if isinstance(images, list) and images:
                image_url = images[0] if isinstance(images[0], str) else images[0].get("url", "")

            return Listing(
                id=self._make_id("carmax", str(stock_no), str(price)),
                source=self.source,
                title=title,
                year=year,
                make=make,
                model=model,
                trim=trim,
                price=price,
                mileage=int(item.get("mileage", 0)),
                exterior_color=item.get("exteriorColor", ""),
                interior_color=item.get("interiorColor", ""),
                vin=item.get("vin", ""),
                dealer_name="CarMax",
                location=item.get("storeName", ""),
                listing_url=listing_url,
                image_url=image_url,
                condition="Used",
            )
        except (ValueError, TypeError):
            return None

    def _parse_card(self, card: object, params: SearchParams) -> Listing | None:
        try:
            title_el = card.select_one(".car-title, h3, [data-testid='car-title']")
            price_el = card.select_one(".car-price, [data-testid='car-price']")
            mileage_el = card.select_one(".car-mileage, [data-testid='car-mileage']")
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
                id=self._make_id("carmax", title, str(price)),
                source=self.source,
                title=title,
                year=year,
                make=params.make,
                model=params.model,
                price=price,
                mileage=mileage,
                dealer_name="CarMax",
                image_url=img_el.get("src", "") if img_el else "",
                listing_url=href,
                condition="Used",
            )
        except (ValueError, TypeError, AttributeError):
            return None
