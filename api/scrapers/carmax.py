from __future__ import annotations

import logging

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
            uri = f"/cars/{make}/{model}"

            api_url = f"{self.base_url}/cars/api/search/run"
            query: dict[str, str] = {
                "uri": uri,
                "skip": "0",
                "take": "100",
                "zipCode": params.zip_code,
                "radius": str(params.radius_miles),
            }

            resp = await self._get_json(api_url, params=query)
            data = resp.json()
            items = data.get("items", [])

            listings: list[Listing] = []
            for item in items:
                listing = self._parse_item(item, params)
                if listing:
                    listings.append(listing)

            logger.info(f"CarMax: {len(listings)} listings from API")
            return listings

        except Exception:
            logger.exception("CarMax scrape failed")
            return []

    def _parse_item(self, item: dict, params: SearchParams) -> Listing | None:
        try:
            price = int(item.get("basePrice", 0) or 0)
            if price <= 0:
                return None

            year = int(item.get("year", 0))
            if year <= 0:
                return None

            make = item.get("make", params.make)
            model = item.get("model", params.model)
            trim = item.get("trim", "")

            title = f"{year} {make} {model}"
            if trim:
                title += f" {trim}"

            stock = str(item.get("stockNumber", ""))
            listing_url = f"{self.base_url}/car/{stock}" if stock else ""

            image_url = item.get("heroImageUrl", "")

            location_parts = []
            city = item.get("storeCity", "")
            state = item.get("stateAbbreviation", "")
            store_name = item.get("storeName", "")
            if city and state:
                location_parts.append(f"{city}, {state}")
            elif store_name:
                location_parts.append(store_name)
            location = " ".join(location_parts)

            dealer_name = "CarMax"
            if store_name:
                dealer_name = f"CarMax {store_name}"

            dealer_rating = item.get("averageRating")

            fuel_type = item.get("engineType", item.get("fuelType", ""))
            drivetrain = item.get("driveTrain", "")
            transmission = item.get("transmission", "")
            engine_size = item.get("engineSize", "")
            cylinders = item.get("cylinders")
            engine = f"{engine_size} {cylinders}cyl".strip() if engine_size and cylinders else (engine_size or "")

            raw_distance = item.get("distance")
            distance_miles = round(raw_distance) if raw_distance is not None else None

            has_price_drop = item.get("hasPriceDrop", False)
            condition = "Used"
            if item.get("isNewArrival"):
                condition = "Used"

            return Listing(
                id=self._make_id("carmax", stock, str(price)),
                source=self.source,
                title=title,
                year=year,
                make=make,
                model=model,
                trim=trim,
                price=price,
                mileage=int(item.get("mileage", 0) or 0),
                exterior_color=item.get("exteriorColor", ""),
                interior_color=item.get("interiorColor", ""),
                drivetrain=drivetrain,
                fuel_type=fuel_type,
                transmission=transmission,
                engine=engine,
                vin=item.get("vin", ""),
                dealer_name=dealer_name,
                dealer_rating=float(dealer_rating) if dealer_rating else None,
                location=location,
                distance_miles=distance_miles,
                listing_url=listing_url,
                image_url=image_url,
                condition=condition,
            )
        except (ValueError, TypeError, KeyError):
            return None
