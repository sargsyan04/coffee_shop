from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import db_session
from src.core.file_storage import save_image, delete_image
from src.schemas.product import ProductCreate, ProductResponse
from src.models.product import Product
from src.models.category import Category

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(db_session),
):

    result = await db.execute(
        select(Category).where(Category.id.in_(data.category_ids))
    )

    categories = result.scalars().all()

    if len(categories) != len(data.category_ids):
        raise HTTPException(
            status_code=404,
            detail="Категория не найдена"
        )

    product = Product(
        name=data.name,
        price=data.price,
        image_url=None
    )

    product.categories.extend(categories)

    db.add(product)
    await db.commit()
    await db.refresh(product)

    result = await db.execute(
        select(Product)
        .options(selectinload(Product.categories))
        .where(Product.id == product.id)
    )

    product = result.scalar_one()

    return product

@router.get("/", response_model=list[ProductResponse])
async def get_products(db: AsyncSession = Depends(db_session)):
    result = await db.execute(
        select(Product).options(
            selectinload(Product.category),
            selectinload(Product.tags),
        )
    )
    products = result.scalars().all()
    return products


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
        raise HTTPException(404, "Товар не найден")
    return product

@router.post("/{product_id}/image", response_model=ProductResponse)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(db_session),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(404, "Товар не найден")

    delete_image(product.image_url)
    product.image_url = save_image(file, folder="products")

    await db.commit()
    await db.refresh(product)
    return product
