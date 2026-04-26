from __future__ import annotations

import json
import logging
import re

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
                "numRecords": "100",
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

        match = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            html,
            re.DOTALL,
        )
        if not match:
            logger.warning("AutoTrader: __NEXT_DATA__ not found")
            return []

        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            logger.warning("AutoTrader: invalid JSON in __NEXT_DATA__")
            return []

        eggs = (
            data.get("props", {})
            .get("pageProps", {})
            .get("__eggsState", {})
        )
        inventory = eggs.get("inventory", {})

        for listing_id, item in inventory.items():
            listing = self._parse_item(item, params)
            if listing:
                listings.append(listing)

        logger.info(f"AutoTrader: parsed {len(listings)} listings")
        return listings

    def _parse_item(self, item: dict, params: SearchParams) -> Listing | None:
        try:
            pricing = item.get("pricingDetail") or {}
            price = int(
                pricing.get("primary")
                or pricing.get("salePrice")
                or pricing.get("dealerDiscountedPrice")
                or pricing.get("msrp")
                or 0
            )
            if price <= 0:
                return None

            year = int(item.get("year", 0))
            if year <= 0:
                return None

            raw_make = item.get("make", params.make)
            make = raw_make.get("name", str(raw_make)) if isinstance(raw_make, dict) else str(raw_make)
            raw_model = item.get("model", params.model)
            model = raw_model.get("name", str(raw_model)) if isinstance(raw_model, dict) else str(raw_model)
            raw_trim = item.get("trim", item.get("atTrim", ""))
            trim = raw_trim.get("name", str(raw_trim)) if isinstance(raw_trim, dict) else str(raw_trim)

            title = f"{year} {make} {model}"
            if trim:
                title += f" {trim}"

            mileage_raw = item.get("mileage", 0)
            if isinstance(mileage_raw, dict):
                mileage_str = str(mileage_raw.get("value", "0"))
                mileage = int(re.sub(r"[^\d]", "", mileage_str) or 0)
            elif isinstance(mileage_raw, str):
                mileage = int(re.sub(r"[^\d]", "", mileage_raw) or 0)
            else:
                mileage = int(mileage_raw or 0)

            color = item.get("color") or {}
            ext_color = color.get("exteriorColorSimple", color.get("exteriorColor", ""))
            int_color = color.get("interiorColorSimple", color.get("interiorColor", ""))

            drive_type = item.get("driveType", {})
            drivetrain = drive_type.get("description", "") if isinstance(drive_type, dict) else str(drive_type)

            fuel_info = item.get("fuelType", {})
            fuel_type = fuel_info.get("group", fuel_info.get("name", "")) if isinstance(fuel_info, dict) else str(fuel_info)

            engine_info = item.get("engine", {})
            engine = engine_info.get("name", "") if isinstance(engine_info, dict) else str(engine_info)

            transmission = item.get("transmission", {})
            trans_str = transmission.get("name", "") if isinstance(transmission, dict) else str(transmission)

            images = item.get("images", {})
            image_url = ""
            if isinstance(images, dict):
                sources = images.get("sources", [])
                if sources:
                    image_url = sources[0].get("src", "")
            elif isinstance(images, list) and images:
                image_url = images[0] if isinstance(images[0], str) else images[0].get("url", "")

            listing_id = str(item.get("id", ""))
            vdp_base = item.get("vdpBaseUrl", "")
            listing_url = f"{self.base_url}{vdp_base}" if vdp_base else ""
            if not listing_url and listing_id:
                listing_url = f"{self.base_url}/cars-for-sale/vehicledetails.xhtml?listingId={listing_id}"

            days_on_site = item.get("daysOnSite")

            dealer_name = item.get("ownerName", item.get("dealerName", ""))
            city = item.get("city", "")
            state = item.get("state", "")
            location = f"{city}, {state}".strip(", ")

            condition = "New" if item.get("listingType") == "NEW" else "Used"
            list_types = item.get("listingTypes", [])
            if "CPO" in list_types:
                condition = "Certified Pre-Owned"

            return Listing(
                id=self._make_id("autotrader", listing_id, str(price)),
                source=self.source,
                title=title,
                year=year,
                make=make,
                model=model,
                trim=trim,
                price=price,
                mileage=mileage,
                exterior_color=ext_color,
                interior_color=int_color,
                drivetrain=drivetrain,
                fuel_type=fuel_type,
                transmission=trans_str,
                engine=engine,
                vin=item.get("vin", ""),
                dealer_name=dealer_name,
                location=location,
                days_on_market=days_on_site,
                image_url=image_url,
                listing_url=listing_url,
                condition=condition,
            )
        except (ValueError, TypeError, KeyError, AttributeError):
            return None
