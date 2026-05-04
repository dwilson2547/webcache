"""Tests for LocalStorage backend in isolation."""

import lz4.frame
import pytest

from app.storage.local import LocalStorage


@pytest.fixture()
def storage(tmp_path):
    return LocalStorage(tmp_path / "cache")


def _compress(text: str) -> bytes:
    return lz4.frame.compress(text.encode())


class TestLocalStorage:
    def test_write_and_read(self, storage):
        data = _compress("hello world")
        storage.write("abc123", data)
        assert storage.read("abc123") == data

    def test_exists_true(self, storage):
        storage.write("abc123", _compress("data"))
        assert storage.exists("abc123") is True

    def test_exists_false(self, storage):
        assert storage.exists("doesnotexist") is False

    def test_read_missing_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.read("missing")

    def test_delete_removes_file(self, storage):
        storage.write("abc123", _compress("data"))
        storage.delete("abc123")
        assert storage.exists("abc123") is False

    def test_delete_noop_when_missing(self, storage):
        storage.delete("never_written")  # should not raise

    def test_creates_directory_on_init(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c"
        s = LocalStorage(deep)
        assert deep.exists()

    def test_file_named_by_hash(self, tmp_path):
        s = LocalStorage(tmp_path / "cache")
        s.write("deadbeef", _compress("x"))
        assert (tmp_path / "cache" / "deadbeef.lz4").exists()
