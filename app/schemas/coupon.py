from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CouponCreate(BaseModel):
    code: str
    discount_type: str = "percent"   # percent | fixed
    discount_value: float
    min_order_amount: float = 0.0
    max_uses: Optional[int] = None
    is_active: bool = True
    expires_at: Optional[datetime] = None


class CouponOut(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: float
    min_order_amount: float
    max_uses: Optional[int]
    used_count: int
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class CouponValidate(BaseModel):
    code: str
    order_amount: float
