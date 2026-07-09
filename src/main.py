import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routers.product import router as product_router

app = FastAPI(
    title="Coffee Shop API",
    description="Coffee Shop management system",
    version="1.0.0",
)

app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(product_router)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8080, reload=True)