from __future__ import annotations

import logging

from models import Listing, SearchParams, Source
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CarsComScraper(BaseScraper):
    """Cars.com scraper — currently blocked by Cloudflare challenge."""

    source = Source.CARS_COM
    base_url = "https://www.cars.com"

    async def search(self, params: SearchParams) -> list[Listing]:
        # Cars.com uses Cloudflare managed challenges that block
        # non-browser requests. Skipping until proxy/browser solution
        # is implemented.
        logger.debug("Cars.com: skipped (Cloudflare challenge)")
        return []
