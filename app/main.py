from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import async_session
from app.api.v1.router import api_router
from app.seed.seed_db import seed_database
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session() as session:
        await seed_database(session)

    yield


app = FastAPI(
    title="Recipe Sharing API",
    description="A recipe sharing platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
