from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.schemas.product import ProductBrief


class ReviewBase(BaseModel):
    rating: int
    comment: str


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    comment: str


class ReviewResponse(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product: ProductBrief
    created_at: datetime
