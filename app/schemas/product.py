from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Category ──────────────────────────────────────────────
class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    image_url: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Product ───────────────────────────────────────────────
class ProductCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    price: float
    sale_price: Optional[float] = None
    stock: int = 0
    sku: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[str] = None   # JSON string
    is_active: bool = True
    is_featured: bool = False
    category_id: Optional[int] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    sale_price: Optional[float] = None
    stock: Optional[int] = None
    sku: Optional[str] = None
    image_url: Optional[str] = None
    images: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    category_id: Optional[int] = None


class ProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str]
    price: float
    sale_price: Optional[float]
    stock: int
    sku: Optional[str]
    image_url: Optional[str]
    images: Optional[str]
    is_active: bool
    is_featured: bool
    category_id: Optional[int]
    category: Optional[CategoryOut]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProductListOut(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[ProductOut]
