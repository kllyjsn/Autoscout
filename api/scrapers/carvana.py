from __future__ import annotations

import logging

from models import Listing, SearchParams, Source
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CarvanaScraper(BaseScraper):
    """Carvana scraper — currently blocked by Cloudflare challenge."""

    source = Source.CARVANA
    base_url = "https://www.carvana.com"

    async def search(self, params: SearchParams) -> list[Listing]:
        # Carvana uses Cloudflare managed challenges that block
        # non-browser requests. Skipping until proxy/browser solution
        # is implemented.
        logger.debug("Carvana: skipped (Cloudflare challenge)")
        return []
