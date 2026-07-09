from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import db_session
from src.core.file_storage import save_image, delete_image
from src.schemas.product import ProductCreate, ProductOut
from src.models.product import Product

router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=ProductOut, status_code=201)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(db_session),):

    product = Product(
        name=data.name,
        price=data.price,
        category_id=data.category_id,
        image_url=None,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    return product

@router.post("/{product_id}/image", response_model=ProductOut)
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
