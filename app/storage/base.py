from abc import ABC, abstractmethod


class BaseStorage(ABC):
    @abstractmethod
    def write(self, content_hash: str, compressed_data: bytes) -> None:
        """Write compressed page data; filename is content_hash."""

    @abstractmethod
    def read(self, content_hash: str) -> bytes:
        """Return compressed bytes for content_hash. Raise FileNotFoundError if absent."""

    @abstractmethod
    def delete(self, content_hash: str) -> None:
        """Delete stored file. No-op if it doesn't exist."""

    @abstractmethod
    def exists(self, content_hash: str) -> bool:
        """Return True if a file for content_hash exists."""
