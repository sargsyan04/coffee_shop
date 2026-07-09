from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    name: str
    price: float
    category_id: int


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # позволяет строить схему прямо из ORM-объекта

    id: int
    name: str
    price: float
    category_id: int
    image_url: str | None = None