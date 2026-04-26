from __future__ import annotations

import abc
import hashlib
import logging
from typing import ClassVar

from curl_cffi import requests as cffi_requests

from models import Listing, SearchParams, Source

logger = logging.getLogger(__name__)


class BaseScraper(abc.ABC):
    source: ClassVar[Source]
    base_url: ClassVar[str]

    @abc.abstractmethod
    async def search(self, params: SearchParams) -> list[Listing]:
        ...

    def _get(self, url: str, **kwargs: object) -> cffi_requests.Response:
        """HTTP GET with browser TLS fingerprint impersonation."""
        resp = cffi_requests.get(
            url,
            impersonate="chrome120",
            timeout=20,
            **kwargs,
        )
        resp.raise_for_status()
        return resp

    def _get_json(self, url: str, **kwargs: object) -> cffi_requests.Response:
        """HTTP GET expecting JSON response."""
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/json")
        return self._get(url, headers=headers, **kwargs)

    def _make_id(self, *parts: str) -> str:
        raw = "|".join(str(p) for p in parts)
        return hashlib.md5(raw.encode()).hexdigest()[:12]
