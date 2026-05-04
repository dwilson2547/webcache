"""
API integration tests — run against a local-storage in-memory test app.
"""

from datetime import datetime, timezone

import pytest

LOOKUP_TIME = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc).isoformat()

PAGE_A = {
    "url": "https://example.com/page-a",
    "content": "<html><body>Page A content</body></html>",
    "client_name": "test_scraper",
    "lookup_time": LOOKUP_TIME,
}

PAGE_B = {
    "url": "https://example.com/page-b?ref=1",
    "content": "<html><body>Page B content (different)</body></html>",
    "client_name": "test_scraper",
    "lookup_time": LOOKUP_TIME,
}


class TestStoreAndRetrieve:
    def test_store_returns_201(self, client):
        response = client.post("/cache", json=PAGE_A)
        assert response.status_code == 201
        data = response.json()
        assert data["url"] == PAGE_A["url"]
        assert data["client_name"] == PAGE_A["client_name"]
        assert "content_hash" in data

    def test_store_same_content_returns_200(self, client):
        client.post("/cache", json=PAGE_A)
        response = client.post("/cache", json=PAGE_A)
        assert response.status_code == 200

    def test_get_by_url_returns_content(self, client):
        client.post("/cache", json=PAGE_A)
        response = client.get("/cache", params={"url": PAGE_A["url"]})
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == PAGE_A["content"]

    def test_get_by_url_404(self, client):
        response = client.get("/cache", params={"url": "https://notcached.example.com"})
        assert response.status_code == 404

    def test_get_by_hash(self, client):
        store_resp = client.post("/cache", json=PAGE_A)
        content_hash = store_resp.json()["content_hash"]
        response = client.get(f"/cache/{content_hash}")
        assert response.status_code == 200
        assert response.json()["content"] == PAGE_A["content"]

    def test_get_by_hash_404(self, client):
        response = client.get("/cache/" + "a" * 64)
        assert response.status_code == 404


class TestSearch:
    def test_search_returns_matching_entries(self, client):
        client.post("/cache", json=PAGE_A)
        client.post("/cache", json=PAGE_B)
        response = client.get("/cache/search", params={"url_contains": "example.com"})
        assert response.status_code == 200
        urls = [e["url"] for e in response.json()]
        assert PAGE_A["url"] in urls
        assert PAGE_B["url"] in urls

    def test_search_query_param_substring(self, client):
        """Search by base URL without query string should match URLs with query params."""
        client.post("/cache", json=PAGE_B)
        response = client.get(
            "/cache/search", params={"url_contains": "example.com/page-b"}
        )
        assert response.status_code == 200
        urls = [e["url"] for e in response.json()]
        assert PAGE_B["url"] in urls

    def test_search_no_match_returns_empty_list(self, client):
        response = client.get(
            "/cache/search", params={"url_contains": "this-will-never-match-xyz"}
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_search_does_not_return_content(self, client):
        client.post("/cache", json=PAGE_A)
        response = client.get("/cache/search", params={"url_contains": "example"})
        for entry in response.json():
            assert "content" not in entry


class TestDelete:
    def test_delete_removes_entry(self, client):
        store_resp = client.post("/cache", json=PAGE_A)
        content_hash = store_resp.json()["content_hash"]

        del_resp = client.delete(f"/cache/{content_hash}")
        assert del_resp.status_code == 204

        get_resp = client.get("/cache", params={"url": PAGE_A["url"]})
        assert get_resp.status_code == 404

    def test_delete_404(self, client):
        response = client.delete("/cache/" + "b" * 64)
        assert response.status_code == 404


class TestHealth:
    def test_health_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
