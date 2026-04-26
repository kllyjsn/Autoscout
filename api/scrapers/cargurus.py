from __future__ import annotations

import json
import logging
import re

from bs4 import BeautifulSoup

from models import Listing, SearchParams, Source
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# CarGurus entity IDs for common makes/models
ENTITY_MAP: dict[str, str] = {
    "rivian_r1s": "d2767",
    "rivian_r1t": "d2766",
    "tesla_model_y": "d2364",
    "tesla_model_3": "d2171",
    "tesla_model_x": "d1967",
    "tesla_model_s": "d1566",
    "ford_f-150_lightning": "d2843",
    "chevrolet_bolt_ev": "d2171",
    "bmw_ix": "d2820",
    "mercedes-benz_eqs": "d2810",
}


class CarGurusScraper(BaseScraper):
    source = Source.CARGURUS
    base_url = "https://www.cargurus.com"

    async def search(self, params: SearchParams) -> list[Listing]:
        try:
            entity_key = f"{params.make.lower()}_{params.model.lower()}"
            entity_id = ENTITY_MAP.get(entity_key, "d2767")

            url = (
                f"{self.base_url}/Cars/inventorylisting/"
                f"viewDetailsFilterViewInventoryListing.action"
            )
            query_params = {
                "sourceContext": "carGurusHomePage_false_0",
                "entitySelectingHelper.selectedEntity": entity_id,
                "zip": params.zip_code,
                "distance": str(params.radius_miles),
                "startYear": str(params.year_min or ""),
                "endYear": str(params.year_max or ""),
                "minPrice": str(params.price_min or ""),
                "maxPrice": str(params.price_max or ""),
                "maxMileage": str(params.mileage_max or ""),
            }
            # Remove empty params
            query_params = {k: v for k, v in query_params.items() if v}

            resp = await self._get(url, params=query_params)
            return self._parse(resp.text, params)

        except Exception:
            logger.exception("CarGurus scrape failed")
            return []

    def _parse(self, html: str, params: SearchParams) -> list[Listing]:
        listings: list[Listing] = []
        soup = BeautifulSoup(html, "lxml")

        # Try to find JSON-LD structured data first
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict) and data.get("@type") == "ItemList":
                    for item in data.get("itemListElement", []):
                        offer = item.get("item", {})
                        listing = self._parse_jsonld_item(offer, params)
                        if listing:
                            listings.append(listing)
            except (json.JSONDecodeError, KeyError):
                continue

        if listings:
            return listings

        # Fall back to HTML parsing
        cards = soup.select('[data-testid="srp-tile-card"], .cg-dealFinder-result, .listing-row')
        for card in cards:
            listing = self._parse_card(card, params)
            if listing:
                listings.append(listing)

        # Try parsing from embedded JS state
        if not listings:
            listings = self._parse_js_state(html, params)

        return listings

    def _parse_jsonld_item(self, item: dict, params: SearchParams) -> Listing | None:
        try:
            offers = item.get("offers", {})
            price_str = offers.get("price", "0")
            price = int(float(str(price_str).replace(",", "").replace("$", "")))
            if price <= 0:
                return None

            name = item.get("name", "")
            year = int(item.get("vehicleModelDate", item.get("modelDate", 0)))
            mileage_str = item.get("mileageFromOdometer", {})
            if isinstance(mileage_str, dict):
                mileage = int(float(str(mileage_str.get("value", "0")).replace(",", "")))
            else:
                mileage = int(float(str(mileage_str).replace(",", "")))

            return Listing(
                id=self._make_id("cargurus", name, str(price)),
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
                listing_url=item.get("url", ""),
                image_url=item.get("image", ""),
                dealer_name=offers.get("seller", {}).get("name", ""),
                location=offers.get("seller", {}).get("address", {}).get("addressLocality", ""),
            )
        except (ValueError, TypeError):
            return None

    def _parse_card(self, card: object, params: SearchParams) -> Listing | None:
        try:
            title_el = card.select_one("h4, .listing-title, [data-testid='srp-tile-title']")
            price_el = card.select_one(".price, [data-testid='srp-tile-price'], .cg-dealFinder-result-stats-price")
            mileage_el = card.select_one(".mileage, [data-testid='srp-tile-mileage']")
            dealer_el = card.select_one(".dealer-name, [data-testid='srp-tile-dealer-name']")
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

            href = link_el.get("href", "") if link_el else ""
            if href and not href.startswith("http"):
                href = f"{self.base_url}{href}"

            return Listing(
                id=self._make_id("cargurus", title, str(price)),
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

    def _parse_js_state(self, html: str, params: SearchParams) -> list[Listing]:
        listings: list[Listing] = []
        # CarGurus embeds listing data in window.__INITIAL_STATE__ or similar
        patterns = [
            r'"listings"\s*:\s*(\[.*?\])\s*[,}]',
            r'"results"\s*:\s*(\[.*?\])\s*[,}]',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    for item in data[:50]:
                        listing = self._parse_js_item(item, params)
                        if listing:
                            listings.append(listing)
                    if listings:
                        return listings
                except (json.JSONDecodeError, TypeError):
                    continue
        return listings

    def _parse_js_item(self, item: dict, params: SearchParams) -> Listing | None:
        try:
            price = int(item.get("price", item.get("listPrice", 0)))
            if price <= 0:
                return None

            return Listing(
                id=self._make_id("cargurus", str(item.get("id", "")), str(price)),
                source=self.source,
                title=f"{item.get('year', '')} {params.make} {params.model}",
                year=int(item.get("year", 2024)),
                make=params.make,
                model=params.model,
                trim=item.get("trim", ""),
                price=price,
                mileage=int(item.get("mileage", 0)),
                exterior_color=item.get("exteriorColor", ""),
                vin=item.get("vin", ""),
                dealer_name=item.get("dealerName", ""),
                location=f"{item.get('city', '')}, {item.get('state', '')}",
                listing_url=item.get("url", item.get("listingUrl", "")),
                image_url=item.get("imageUrl", item.get("mainPictureUrl", "")),
                days_on_market=item.get("daysOnMarket"),
            )
        except (ValueError, TypeError):
            return None
