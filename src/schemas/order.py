from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime

from src.core.enums import OrderStatus


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, gt=0)

class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal

class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    items: list[OrderItemResponse]
    total_price: Decimal
    created_at: datetime


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
