import hashlib
from datetime import UTC, datetime

import lz4.frame
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..metrics import compressed_bytes, lookup_total, store_total
from ..models import CacheEntry
from ..schemas import CacheEntryCreate, CacheEntryFull, CacheEntryMeta
from ..storage import get_storage

router = APIRouter(prefix="/cache", tags=["cache"])


def _compute_hash(content: str) -> str:
    return hashlib.blake2b(content.encode(), digest_size=32).hexdigest()


def _decompress(content_hash: str) -> str:
    storage = get_storage()
    try:
        compressed = storage.read(content_hash)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Cache file not found")
    return lz4.frame.decompress(compressed).decode()


@router.post("", response_model=CacheEntryMeta, status_code=201)
def store_page(entry: CacheEntryCreate, db: Session = Depends(get_db)):
    """
    Store a web page.  If the identical content (same hash) is already cached
    the existing record is returned with HTTP 200 and nothing is written again.
    """
    content_hash = _compute_hash(entry.content)

    existing = db.query(CacheEntry).filter(CacheEntry.content_hash == content_hash).first()
    if existing:
        from fastapi.responses import JSONResponse
        from fastapi.encoders import jsonable_encoder

        store_total.labels(result="duplicate").inc()
        # Return 200 so callers can distinguish "stored now" (201) from "already existed" (200)
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(CacheEntryMeta.model_validate(existing)),
        )

    compressed = lz4.frame.compress(entry.content.encode())
    compressed_bytes.observe(len(compressed))
    get_storage().write(content_hash, compressed)

    db_entry = CacheEntry(
        url=entry.url,
        content_hash=content_hash,
        client_name=entry.client_name,
        lookup_time=entry.lookup_time,
        created_at=datetime.now(UTC),
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    store_total.labels(result="created").inc()
    return db_entry


@router.get("/search", response_model=list[CacheEntryMeta])
def search_by_url(url_contains: str, db: Session = Depends(get_db)):
    """
    Return metadata for all entries whose URL contains `url_contains`.
    Useful for matching a base URL across different query-parameter variants.
    """
    entries = (
        db.query(CacheEntry)
        .filter(CacheEntry.url.contains(url_contains))
        .order_by(CacheEntry.created_at.desc())
        .all()
    )
    return entries


@router.get("", response_model=CacheEntryFull)
def get_by_url(url: str, db: Session = Depends(get_db)):
    """Return the most recently cached entry for an exact URL, including content."""
    entry = (
        db.query(CacheEntry)
        .filter(CacheEntry.url == url)
        .order_by(CacheEntry.created_at.desc())
        .first()
    )
    if not entry:
        lookup_total.labels(result="miss").inc()
        raise HTTPException(status_code=404, detail="Cache entry not found")

    content = _decompress(entry.content_hash)
    lookup_total.labels(result="hit").inc()
    return CacheEntryFull(**CacheEntryMeta.model_validate(entry).model_dump(), content=content)


@router.get("/{content_hash}", response_model=CacheEntryFull)
def get_by_hash(content_hash: str, db: Session = Depends(get_db)):
    """Return a specific cached entry by its content hash, including content."""
    entry = db.query(CacheEntry).filter(CacheEntry.content_hash == content_hash).first()
    if not entry:
        lookup_total.labels(result="miss").inc()
        raise HTTPException(status_code=404, detail="Cache entry not found")

    content = _decompress(entry.content_hash)
    lookup_total.labels(result="hit").inc()
    return CacheEntryFull(**CacheEntryMeta.model_validate(entry).model_dump(), content=content)


@router.delete("/{content_hash}", status_code=204)
def delete_entry(content_hash: str, db: Session = Depends(get_db)):
    """Delete a cached entry and its associated file."""
    entry = db.query(CacheEntry).filter(CacheEntry.content_hash == content_hash).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Cache entry not found")

    get_storage().delete(content_hash)
    db.delete(entry)
    db.commit()
