from pydantic import BaseModel, ConfigDict

from src.schemas.category import CategoryResponse
from src.schemas.tag import TagResponse
from decimal import Decimal

class ProductCreate(BaseModel):
    name: str
    price: Decimal
    category_id: int | None = None
    tag_ids: list[int] = []


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    category: CategoryResponse | None = None
    tags: list["TagResponse"] = []
    image_url: str | None = None
