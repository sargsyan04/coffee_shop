from pydantic import BaseModel, ConfigDict
from src.schemas.category import CategoryResponse
from decimal import Decimal


class ProductCreate(BaseModel):
    name: str
    price: Decimal
    category_ids: list[int]


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    image_url: str | None = None
    categories: list[CategoryResponse]