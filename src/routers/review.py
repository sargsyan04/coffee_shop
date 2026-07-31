from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import db_session
from src.models import Product, Review, User
from src.schemas import ReviewCreate, ReviewResponse
from src.validators import get_current_active_user

router = APIRouter(prefix="/review", tags=["Reviews"])


@router.get("/user_reviews", response_model=list[ReviewResponse])
async def get_my_reviews(
        current_user: User = Depends(get_current_active_user),
        session: AsyncSession = Depends(db_session)
):
    stmt = (
        select(Review)
        .where(Review.user_id == current_user.id)
        .options(selectinload(Review.product))
    )
    result = await session.scalars(stmt)
    return result.all()


@router.get("/{product_id}/product_reviews", response_model=list[ReviewResponse])
async def get_product_reviews(
        product_id: int,
        session: AsyncSession = Depends(db_session)
):
    stmt = (
        select(Review)
        .where(Review.product_id == product_id)
        .options(selectinload(Review.product))
    )
    result = await session.scalars(stmt)
    return result.all()


@router.post("/{product_id}", response_model=ReviewResponse)
async def create_review(
        product_id: int,
        payload: ReviewCreate,
        current_user: User = Depends(get_current_active_user),
        session: AsyncSession = Depends(db_session)
):
    stmt = select(Product).where(Product.id == product_id)
    product = await session.scalar(stmt)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    review = Review(
        user_id=current_user.id,
        product_id=product.id,
        rating=payload.rating,
        comment=payload.comment
    )

    session.add(review)
    await session.commit()
    await session.refresh(review, attribute_names=["product"])
    return review