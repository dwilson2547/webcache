from datetime import datetime
from typing import Optional

import httpx


class WebCacheClient:
    """
    Python client for the WebCache REST API.

    Usage::

        from webcache_client import WebCacheClient

        client = WebCacheClient("http://localhost:8000")
        client.store(url="https://example.com", content="<html>…</html>", client_name="my_scraper")
        entry = client.get(url="https://example.com")
        results = client.search(url_contains="example.com")
        client.delete(content_hash=entry["content_hash"])
    """

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self._http = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def store(
        self,
        url: str,
        content: str,
        client_name: str,
        lookup_time: Optional[datetime] = None,
    ) -> dict:
        """
        Cache a web page.

        Returns the cache entry metadata dict.
        HTTP 201 → newly stored; HTTP 200 → already existed (same content).
        """
        payload = {
            "url": url,
            "content": content,
            "client_name": client_name,
            "lookup_time": (lookup_time or datetime.utcnow()).isoformat(),
        }
        response = self._http.post("/cache", json=payload)
        response.raise_for_status()
        return response.json()

    def delete(self, content_hash: str) -> None:
        """Delete a cached entry by its content hash."""
        response = self._http.delete(f"/cache/{content_hash}")
        response.raise_for_status()

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, url: str) -> Optional[dict]:
        """
        Retrieve the most recent cached entry for an exact URL.

        Returns the full entry dict (including ``content``) or ``None`` if not found.
        """
        response = self._http.get("/cache", params={"url": url})
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def get_by_hash(self, content_hash: str) -> Optional[dict]:
        """Retrieve a cached entry by its content hash. Returns ``None`` if not found."""
        response = self._http.get(f"/cache/{content_hash}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    def search(self, url_contains: str) -> list[dict]:
        """
        Return metadata for all cached entries whose URL contains ``url_contains``.

        Content is not included in search results — call ``get`` or ``get_by_hash``
        to retrieve the full page content.
        """
        response = self._http.get("/cache/search", params={"url_contains": url_contains})
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def health(self) -> dict:
        response = self._http.get("/health")
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
