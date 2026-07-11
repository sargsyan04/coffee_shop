from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int