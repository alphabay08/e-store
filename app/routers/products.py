from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut, ProductListOut

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ProductListOut)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    featured: Optional[bool] = None,
    in_stock: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.is_active == True)

    if category_id:
        q = q.filter(Product.category_id == category_id)
    if search:
        q = q.filter(or_(
            Product.name.ilike(f"%{search}%"),
            Product.description.ilike(f"%{search}%"),
        ))
    if min_price is not None:
        q = q.filter(Product.price >= min_price)
    if max_price is not None:
        q = q.filter(Product.price <= max_price)
    if featured is not None:
        q = q.filter(Product.is_featured == featured)
    if in_stock:
        q = q.filter(Product.stock > 0)

    total = q.count()
    products = q.offset((page - 1) * page_size).limit(page_size).all()

    return ProductListOut(total=total, page=page, page_size=page_size, results=products)


@router.get("/featured", response_model=list)
def get_featured(limit: int = 8, db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.is_featured == True, Product.is_active == True).limit(limit).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


@router.get("/slug/{slug}", response_model=ProductOut)
def get_product_by_slug(slug: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.slug == slug, Product.is_active == True).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    return p


# ── Admin only ────────────────────────────────────────────
@router.post("", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    if payload.slug and db.query(Product).filter(Product.slug == payload.slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")
    p = Product(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    p.is_active = False   # soft delete
    db.commit()


@router.patch("/{product_id}/stock")
def update_stock(product_id: int, stock: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    p.stock = stock
    db.commit()
    return {"product_id": product_id, "new_stock": stock}
