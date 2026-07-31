from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.category import CategoryResponse
from src.schemas.tag import TagResponse


class ProductBase(BaseModel):
    name: str
    price: Decimal = Field(gt=0)


class ProductCreate(ProductBase):
    category_id: int | None = None
    tag_ids: list[int] = []


# --> Minimal product shape for embedding inside other responses
#     (e.g. ReviewResponse.product) — no category/tags/price needed there <--
class ProductBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    image_url: str | None = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: CategoryResponse | None = None
    tags: list["TagResponse"] = []
    image_url: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    price: Decimal | None = Field(None, gt=0)
    category_id: int | None = None
    tag_ids: list[int] | None = None