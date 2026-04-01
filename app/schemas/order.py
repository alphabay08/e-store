from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ShippingAddress(BaseModel):
    name: str
    phone: str
    address: str
    city: str
    province: Optional[str] = None


class OrderCreate(BaseModel):
    shipping: ShippingAddress
    coupon_code: Optional[str] = None
    customer_note: Optional[str] = None


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_image: Optional[str]
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    order_number: str
    customer_id: int
    shipping_name: str
    shipping_phone: str
    shipping_address: str
    shipping_city: str
    shipping_province: Optional[str]
    subtotal: float
    shipping_charges: float
    discount_amount: float
    total_amount: float
    payment_method: str
    payment_status: str
    status: str
    coupon_code: Optional[str]
    customer_note: Optional[str]
    admin_note: Optional[str]
    tracking_number: Optional[str]
    courier: Optional[str]
    items: List[OrderItemOut]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str
    admin_note: Optional[str] = None
    tracking_number: Optional[str] = None
    courier: Optional[str] = None


class OrderListOut(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[OrderOut]
