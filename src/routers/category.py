from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import db_session
from src.schemas.category import CategoryOut, CategoryCreate
from src.models.category import Category

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post('/', response_model=CategoryOut, status_code=201)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(db_session),):

    category = Category(name=data.name)

    db.add(category)
    await db.commit()
    await db.refresh(category)

    return category



