from __future__ import annotations

import json
import logging
import re

from bs4 import BeautifulSoup

from models import Listing, SearchParams, Source
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class AutoTraderScraper(BaseScraper):
    source = Source.AUTOTRADER
    base_url = "https://www.autotrader.com"

    async def search(self, params: SearchParams) -> list[Listing]:
        try:
            make = params.make.lower()
            model = params.model.lower().replace(" ", "-")
            url = f"{self.base_url}/cars-for-sale/all-cars/{make}/{model}"

            query_params: dict[str, str] = {
                "zip": params.zip_code,
                "searchRadius": str(params.radius_miles),
                "numRecords": "50",
                "sortBy": "relevance",
                "firstRecord": "0",
            }
            if params.year_min:
                query_params["startYear"] = str(params.year_min)
            if params.year_max:
                query_params["endYear"] = str(params.year_max)
            if params.price_min:
                query_params["minPrice"] = str(params.price_min)
            if params.price_max:
                query_params["maxPrice"] = str(params.price_max)
            if params.mileage_max:
                query_params["maxMileage"] = str(params.mileage_max)

            resp = await self._get(url, params=query_params)
            return self._parse(resp.text, params)

        except Exception:
            logger.exception("AutoTrader scrape failed")
            return []

    def _parse(self, html: str, params: SearchParams) -> list[Listing]:
        listings: list[Listing] = []
        soup = BeautifulSoup(html, "lxml")

        # AutoTrader embeds data in __NEXT_DATA__ or similar JSON
        for script in soup.find_all("script", id="__NEXT_DATA__"):
            try:
                data = json.loads(script.string or "")
                props = data.get("props", {}).get("pageProps", {})
                results = (
                    props.get("listings", [])
                    or props.get("initialListings", [])
                    or props.get("results", [])
                )
                for item in results[:50]:
                    listing = self._parse_next_item(item, params)
                    if listing:
                        listings.append(listing)
            except (json.JSONDecodeError, KeyError):
                continue

        if listings:
            return listings

        # Try window.__BONNET_DATA__
        match = re.search(
            r'window\.__BONNET_DATA__\s*=\s*({.*?});?\s*</script>',
            html, re.DOTALL,
        )
        if match:
            try:
                data = json.loads(match.group(1))
                for item in data.get("initialResults", {}).get("listings", [])[:50]:
                    listing = self._parse_bonnet_item(item, params)
                    if listing:
                        listings.append(listing)
            except (json.JSONDecodeError, KeyError):
                pass

        if listings:
            return listings

        # HTML fallback
        cards = soup.select(".inventory-listing, [data-cmp='inventoryListing']")
        for card in cards:
            listing = self._parse_card(card, params)
            if listing:
                listings.append(listing)

        return listings

    def _parse_next_item(self, item: dict, params: SearchParams) -> Listing | None:
        try:
            price = int(item.get("pricingDetail", {}).get("primary", 0)
                        or item.get("price", 0)
                        or item.get("derivedPrice", 0))
            if price <= 0:
                return None

            year = int(item.get("year", 2024))
            mileage_str = item.get("mileage", item.get("mileageString", "0"))
            mileage = int(re.sub(r"[^\d]", "", str(mileage_str)) or 0)

            title = f"{year} {item.get('make', params.make)} {item.get('model', params.model)}"
            trim = item.get("trim", "")
            if trim:
                title += f" {trim}"

            listing_url = item.get("clickUrl", item.get("url", ""))
            if listing_url and not listing_url.startswith("http"):
                listing_url = f"{self.base_url}{listing_url}"

            images = item.get("images", {})
            image_url = ""
            if isinstance(images, dict):
                sources = images.get("sources", [])
                if sources:
                    image_url = sources[0].get("src", "")
            elif isinstance(images, list) and images:
                image_url = images[0] if isinstance(images[0], str) else images[0].get("url", "")

            return Listing(
                id=self._make_id("autotrader", str(item.get("id", "")), str(price)),
                source=self.source,
                title=title,
                year=year,
                make=item.get("make", params.make),
                model=item.get("model", params.model),
                trim=trim,
                price=price,
                mileage=mileage,
                exterior_color=item.get("exteriorColor", ""),
                interior_color=item.get("interiorColor", ""),
                vin=item.get("vin", ""),
                dealer_name=item.get("ownerName", item.get("dealerName", "")),
                location=f"{item.get('city', '')}, {item.get('state', '')}".strip(", "),
                listing_url=listing_url,
                image_url=image_url,
                condition=item.get("condition", "Used"),
            )
        except (ValueError, TypeError):
            return None

    def _parse_bonnet_item(self, item: dict, params: SearchParams) -> Listing | None:
        return self._parse_next_item(item, params)

    def _parse_card(self, card: object, params: SearchParams) -> Listing | None:
        try:
            title_el = card.select_one("h2, .text-bold")
            price_el = card.select_one(".first-price, [data-cmp='firstPrice']")
            mileage_el = card.select_one(".text-bold-sm, .item-card-specifications li")
            link_el = card.select_one("a[href]")
            img_el = card.select_one("img")

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
                id=self._make_id("autotrader", title, str(price)),
                source=self.source,
                title=title,
                year=year,
                make=params.make,
                model=params.model,
                price=price,
                mileage=mileage,
                image_url=img_el.get("src", "") if img_el else "",
                listing_url=href,
            )
        except (ValueError, TypeError, AttributeError):
            return None
