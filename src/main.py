from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pathlib import Path

from src.core import session_factory, settings
from src.fixtures import load_super_admin
from src.routers import (
    admin_router,
    cart_router,
    category_router,
    order_router,
    product_router,
    review_router,
    user_router,
)

# Application Lifespan (startup / shutdown hooks)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure the default admin account exists.
    # Reuses the same fixture-based loader as `manage.py createsuperuser
    # --use-fixture`, so there is a single source of truth for how the
    # default admin is created (idempotent — skips if already present).
    async with session_factory() as session:
        await load_super_admin(session)
        await session.commit()

    yield


# App Setup

app = FastAPI(
    title="Coffee Shop API",
    description="Coffee Shop management system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app.mount("/media", StaticFiles(directory="media"), name="media")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

app.mount(
    "/media",
    StaticFiles(directory=PROJECT_ROOT / "frontend" / "media"),
    name="media",
)


# Root Endpoint & Router Registration

@app.get("/")
async def root():
    return {"status": "ok", "message": "Coffee Shop API is running"}


app.include_router(user_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(admin_router)
app.include_router(order_router)
app.include_router(cart_router)
app.include_router(review_router)


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8080, reload=True)
