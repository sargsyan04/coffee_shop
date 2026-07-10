from sqlalchemy import Table, Column, ForeignKey, BIGINT

from src.models.base import BaseModel

product_tag_association = Table(
    "product_tag",
    BaseModel.metadata,
    Column("product_id", ForeignKey("products.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)