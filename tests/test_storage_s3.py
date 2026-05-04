"""
S3 storage tests using a MinIO testcontainer.

These tests are skipped automatically when Docker is unavailable or
the `testcontainers` package is not installed.
"""

import lz4.frame
import pytest

pytestmark = pytest.mark.skipif(
    pytest.importorskip("testcontainers.minio", reason="testcontainers[minio] not installed") is None,
    reason="testcontainers not available",
)


def _compress(text: str) -> bytes:
    return lz4.frame.compress(text.encode())


class TestS3StorageViaMinio:
    """Run the same contract tests as LocalStorage but against a real MinIO bucket."""

    def test_write_and_read(self, s3_client):
        from datetime import datetime, timezone

        payload = {
            "url": "https://s3test.example.com/page",
            "content": "<html>s3 content</html>",
            "client_name": "s3_tester",
            "lookup_time": datetime(2024, 6, 1, tzinfo=timezone.utc).isoformat(),
        }
        store = s3_client.post("/cache", json=payload)
        assert store.status_code == 201

        get = s3_client.get("/cache", params={"url": payload["url"]})
        assert get.status_code == 200
        assert get.json()["content"] == payload["content"]

    def test_dedup_same_content(self, s3_client):
        from datetime import datetime, timezone

        payload = {
            "url": "https://s3test.example.com/dedup",
            "content": "<html>duplicate content</html>",
            "client_name": "s3_tester",
            "lookup_time": datetime(2024, 6, 1, tzinfo=timezone.utc).isoformat(),
        }
        r1 = s3_client.post("/cache", json=payload)
        r2 = s3_client.post("/cache", json=payload)
        assert r1.status_code == 201
        assert r2.status_code == 200
        assert r1.json()["content_hash"] == r2.json()["content_hash"]

    def test_delete(self, s3_client):
        from datetime import datetime, timezone

        payload = {
            "url": "https://s3test.example.com/delete-me",
            "content": "<html>to be deleted</html>",
            "client_name": "s3_tester",
            "lookup_time": datetime(2024, 6, 1, tzinfo=timezone.utc).isoformat(),
        }
        store = s3_client.post("/cache", json=payload)
        content_hash = store.json()["content_hash"]

        del_resp = s3_client.delete(f"/cache/{content_hash}")
        assert del_resp.status_code == 204

        get_resp = s3_client.get("/cache", params={"url": payload["url"]})
        assert get_resp.status_code == 404

    def test_search(self, s3_client):
        from datetime import datetime, timezone

        base = datetime(2024, 6, 1, tzinfo=timezone.utc).isoformat()
        for i in range(3):
            s3_client.post(
                "/cache",
                json={
                    "url": f"https://s3test.example.com/items?id={i}",
                    "content": f"<html>item {i}</html>",
                    "client_name": "s3_tester",
                    "lookup_time": base,
                },
            )

        results = s3_client.get(
            "/cache/search", params={"url_contains": "s3test.example.com/items"}
        )
        assert results.status_code == 200
        assert len(results.json()) == 3
