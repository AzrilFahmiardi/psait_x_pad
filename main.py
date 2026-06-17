from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app import data_loader
from app.routers import manholes, pipes, statistics


@asynccontextmanager
async def lifespan(app: FastAPI):
    data_loader.load_all()
    yield


app = FastAPI(
    title="IPAL Public API",
    description="Public read-only API for IPAL manhole and pipe network data",
    version="1.0.0",
    lifespan=lifespan,
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
