from sqlalchemy import Table, Column, ForeignKey, BIGINT

from src.models.base import BaseModel

product_category_association = Table(
    "product_categories",
    BaseModel.metadata,
    Column("product_id", BIGINT, ForeignKey("products.id"), primary_key=True),
    Column("category_id", BIGINT, ForeignKey("categories.id"), primary_key=True),
)