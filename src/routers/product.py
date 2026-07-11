from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core import db_session
from src.core.file_storage import save_image, delete_image
from src.models import Tag
from src.schemas.product import ProductCreate, ProductResponse
from src.models.product import Product
from src.models.category import Category

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/create", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(db_session),
):
    if data.category_id is not None:
        category = await db.get(Category, data.category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="Категория не найдена")

    tags = []
    if data.tag_ids:
        result = await db.execute(select(Tag).where(Tag.id.in_(data.tag_ids)))
        tags = result.scalars().all()
        if len(tags) != len(data.tag_ids):
            raise HTTPException(status_code=404, detail="Один или несколько тегов не найдены")

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
