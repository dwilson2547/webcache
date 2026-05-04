from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .config import settings
from .database import Base, get_engine
from .metrics import init_storage_info
from .routes.cache import router as cache_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=get_engine())
    init_storage_info(settings.storage_backend.value)
    yield


app = FastAPI(
    title="WebCache",
    description="Centralized web page cold-storage cache with LZ4 compression.",
    version="0.1.0",
    lifespan=lifespan,
)

Instrumentator().instrument(app).expose(app, tags=["ops"])
app.include_router(cache_router)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok"}
