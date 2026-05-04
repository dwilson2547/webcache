from datetime import datetime

from pydantic import BaseModel


class CacheEntryCreate(BaseModel):
    url: str
    content: str
    client_name: str
    lookup_time: datetime


class CacheEntryMeta(BaseModel):
    url: str
    content_hash: str
    client_name: str
    lookup_time: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class CacheEntryFull(CacheEntryMeta):
    content: str
