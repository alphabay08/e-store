from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.coupon import Coupon
from app.schemas.coupon import CouponCreate, CouponOut, CouponValidate

router = APIRouter(prefix="/coupons", tags=["Coupons"])


@router.post("/validate")
def validate_coupon(payload: CouponValidate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    coupon = db.query(Coupon).filter(Coupon.code == payload.code.upper(), Coupon.is_active == True).first()
    if not coupon:
        raise HTTPException(status_code=400, detail="Invalid or inactive coupon")
    if coupon.expires_at and coupon.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Coupon has expired")
    if coupon.max_uses and coupon.used_count >= coupon.max_uses:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")
    if payload.order_amount < coupon.min_order_amount:
        raise HTTPException(status_code=400, detail=f"Minimum order amount is PKR {coupon.min_order_amount}")
    if coupon.discount_type == "percent":
        discount = round(payload.order_amount * coupon.discount_value / 100, 2)
    else:
        discount = min(coupon.discount_value, payload.order_amount)
    return {
        "valid": True,
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "discount_amount": round(discount, 2),
        "new_total": round(payload.order_amount - discount, 2),
    }


@router.get("", response_model=List[CouponOut])
def list_coupons(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


@router.post("", response_model=CouponOut, status_code=201)
def create_coupon(payload: CouponCreate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    if db.query(Coupon).filter(Coupon.code == payload.code.upper()).first():
        raise HTTPException(status_code=400, detail="Coupon code already exists")
    coupon = Coupon(**payload.model_dump())
    coupon.code = coupon.code.upper()
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/{coupon_id}", status_code=204)
def delete_coupon(coupon_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    db.delete(coupon)
    db.commit()
