from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import get_engine, get_session_factory, Base
from .api import videos, jobs, query
from .services.storage import ensure_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up the shared engine + session factory (cached singletons)
    engine = get_engine()
    get_session_factory()
    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Create MinIO bucket if it doesn't exist yet
    ensure_bucket()
    yield
    await engine.dispose()


app = FastAPI(
    title="Video Scene Intelligence API",
    description="Upload videos and query their content with natural language.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router)
app.include_router(jobs.router)
app.include_router(query.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
