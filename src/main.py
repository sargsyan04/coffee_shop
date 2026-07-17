import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.routers import routers
from src.core import session_factory
from src.services import seed_admin_user


# ============================================================
# --> Application Lifespan (startup / shutdown hooks) <--
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --> Startup: seed the initial admin account if none exists yet <--
    async with session_factory() as session:
        await seed_admin_user(session)

    yield


# ============================================================
# --> App Setup <--
# ============================================================

app = FastAPI(
    title="Coffee Shop API",
    description="Coffee Shop management system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory="media"), name="media")


# ============================================================
# --> Root Endpoint & Router Registration <--
# ============================================================

@app.get("/")
async def root():
    return {"status": "ok", "message": "Coffee Shop API is running"}


for router in routers:
    app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, reload=True)