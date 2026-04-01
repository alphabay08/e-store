from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.product import ProductOut


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    total: float = 0.0
    product: Optional[ProductOut]

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_total(cls, item):
        data = cls.model_validate(item)
        data.total = round(item.unit_price * item.quantity, 2)
        return data


class CartOut(BaseModel):
    id: int
    customer_id: int
    items: List[CartItemOut]
    subtotal: float = 0.0
    item_count: int = 0

    class Config:
        from_attributes = True
