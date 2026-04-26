from __future__ import annotations

import abc
import hashlib
import logging
from typing import ClassVar

import httpx

from models import Listing, SearchParams, Source

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


class BaseScraper(abc.ABC):
    source: ClassVar[Source]
    base_url: ClassVar[str]

    @abc.abstractmethod
    async def search(self, params: SearchParams) -> list[Listing]:
        ...

    async def _get(self, url: str, **kwargs: object) -> httpx.Response:
        async with httpx.AsyncClient(
            headers=HEADERS,
            follow_redirects=True,
            timeout=20.0,
        ) as client:
            resp = await client.get(url, **kwargs)
            resp.raise_for_status()
            return resp

    def _make_id(self, *parts: str) -> str:
        raw = "|".join(str(p) for p in parts)
        return hashlib.md5(raw.encode()).hexdigest()[:12]
