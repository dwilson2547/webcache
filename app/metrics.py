from prometheus_client import Counter, Histogram, Info

store_total = Counter(
    "webcache_store_total",
    "Number of page store requests",
    ["result"],  # "created" | "duplicate"
)

lookup_total = Counter(
    "webcache_lookup_total",
    "Number of page lookup requests",
    ["result"],  # "hit" | "miss"
)

compressed_bytes = Histogram(
    "webcache_compressed_bytes",
    "Size of LZ4-compressed page files in bytes",
    buckets=[1_024, 8_192, 32_768, 131_072, 524_288, 2_097_152, 8_388_608],
)

storage_info = Info(
    "webcache_storage",
    "Active storage backend",
)


def init_storage_info(backend: str) -> None:
    """Call once at startup with the configured backend name."""
    storage_info.info({"backend": backend})
