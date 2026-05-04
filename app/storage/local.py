from pathlib import Path

from .base import BaseStorage


class LocalStorage(BaseStorage):
    def __init__(self, base_path: Path) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, content_hash: str) -> Path:
        return self.base_path / f"{content_hash}.lz4"

    def write(self, content_hash: str, compressed_data: bytes) -> None:
        self._path(content_hash).write_bytes(compressed_data)

    def read(self, content_hash: str) -> bytes:
        p = self._path(content_hash)
        if not p.exists():
            raise FileNotFoundError(f"No cache file for hash {content_hash}")
        return p.read_bytes()

    def delete(self, content_hash: str) -> None:
        p = self._path(content_hash)
        if p.exists():
            p.unlink()

    def exists(self, content_hash: str) -> bool:
        return self._path(content_hash).exists()
