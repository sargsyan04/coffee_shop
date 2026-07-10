import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.routers import routers

app = FastAPI(
    title="Coffee Shop API",
    description="Coffee Shop management system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5500",
                   "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory="media"), name="media")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Coffee Shop API is running"}

for router in routers:
    app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, reload=True)