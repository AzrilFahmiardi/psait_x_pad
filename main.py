from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app import data_loader
from app.routers import manholes, pipes, statistics

DESCRIPTION = """
## IPAL Public API
"""

TAGS_METADATA = [
    {
        "name": "statistics",
        "description": "Statistik ringkasan jaringan IPAL — jumlah aset, kondisi, dan status.",
    },
    {
        "name": "manholes",
        "description": "Data titik **manhole** — list, detail, filter, dan export GeoJSON untuk peta.",
    },
    {
        "name": "pipes",
        "description": "Data **jaringan pipa** — list, detail, filter, dan export GeoJSON untuk peta.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_loader.load_all()
    yield


app = FastAPI(
    title="IPAL Public API",
    description=DESCRIPTION,
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
    contact={
        "name": "BPAL Kota Yogyakarta",
        "url": "https://psait-x-pad.onrender.com",
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(statistics.router)
app.include_router(manholes.router)
app.include_router(pipes.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "IPAL Public API"}
