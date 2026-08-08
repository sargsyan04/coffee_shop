import math
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import db_session, delete_image, save_image
from src.models import Tag
from src.models.category import Category
from src.models.product import Product
from src.schemas.common import Page
from src.schemas.product import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])

# Maps the public `sort_by` query value to the column it orders by.
PRODUCT_SORT_COLUMNS = {
    "name": Product.name,
    "price": Product.price,
    "rating": Product.average_rating,
    "popularity": Product.sold_count,
}


@router.post("/create", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(db_session),
):
    if data.category_id is not None:
        category = await db.get(Category, data.category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    tags = []
    if data.tag_ids:
        result = await db.execute(select(Tag).where(Tag.id.in_(data.tag_ids)))
        tags = result.scalars().all()
        if len(tags) != len(data.tag_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more tags were not found",
            )

    product = Product(
        name=data.name,
        price=data.price,
        category_id=data.category_id,
        image_url=None,
    )
    product.tags = tags

    db.add(product)
    await db.commit()
    await db.refresh(product, attribute_names=["category", "tags"])

    return product


@router.get("/", response_model=Page[ProductResponse])
async def get_products(
    db: AsyncSession = Depends(db_session),
    sort_by: Literal["name", "price", "rating", "popularity"] = Query("name", description="Field to sort the menu by."),
    order: Literal["asc", "desc"] = Query("asc", description="Sort direction."),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    column = PRODUCT_SORT_COLUMNS[sort_by]
    direction = column.asc() if order == "asc" else column.desc()

    total = await db.scalar(select(func.count()).select_from(Product))
    total = total or 0
    total_pages = math.ceil(total / page_size) if total else 0

    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.tags),
        )
        .order_by(direction, Product.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    products = result.scalars().all()

    return Page(
        items=products,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(db_session)):
    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.tags),
        )
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.post("/{product_id}/image", response_model=ProductResponse)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(db_session),
):
    stmt = select(Product).options(selectinload(Product.category), selectinload(Product.tags)).where(Product.id == product_id)
    product = await session.scalar(stmt)

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    delete_image(product.image_url)
    product.image_url = save_image(file, filename_prefix="Product", entity_id=product_id, folder="products")

    await session.commit()
    await session.refresh(product)
    return product
