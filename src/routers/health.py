import asyncio

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import db_session
from src.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health(session: AsyncSession = Depends(db_session)):
    try:
        await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=3)
    except (SQLAlchemyError, OSError, TimeoutError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": "down"},
        )

    return {"status": "ok", "database": "up"}
