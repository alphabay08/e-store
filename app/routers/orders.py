import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.coupon import Coupon
from app.models.user import User
from app.schemas.order import OrderCreate, OrderOut, OrderListOut, OrderStatusUpdate
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["Orders"])

SHIPPING_CHARGES = {
    "karachi": 150.0,
    "lahore": 200.0,
    "islamabad": 200.0,
    "rawalpindi": 200.0,
    "default": 250.0,
}


def get_shipping_charge(city: str) -> float:
    return SHIPPING_CHARGES.get(city.lower(), SHIPPING_CHARGES["default"])


def generate_order_number() -> str:
    return "ORD-" + uuid.uuid4().hex[:8].upper()


def apply_coupon(coupon_code: str, subtotal: float, db: Session):
    coupon = db.query(Coupon).filter(Coupon.code == coupon_code.upper(), Coupon.is_active == True).first()
    if not coupon:
        raise HTTPException(status_code=400, detail="Invalid or inactive coupon code")
    if coupon.expires_at and coupon.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Coupon has expired")
    if coupon.max_uses and coupon.used_count >= coupon.max_uses:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")
    if subtotal < coupon.min_order_amount:
        raise HTTPException(status_code=400, detail=f"Minimum order amount for this coupon is PKR {coupon.min_order_amount}")
    if coupon.discount_type == "percent":
        discount = round(subtotal * coupon.discount_value / 100, 2)
    else:
        discount = min(coupon.discount_value, subtotal)
    return coupon, round(discount, 2)


@router.post("", response_model=OrderOut, status_code=201)
def place_order(payload: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = db.query(Cart).filter(Cart.customer_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Your cart is empty")

    subtotal = 0.0
    for item in cart.items:
        if item.product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"'{item.product.name}' only has {item.product.stock} units in stock")
        subtotal += item.unit_price * item.quantity
    subtotal = round(subtotal, 2)

    shipping_charges = get_shipping_charge(payload.shipping.city)
    discount_amount = 0.0
    coupon_obj = None

    if payload.coupon_code:
        coupon_obj, discount_amount = apply_coupon(payload.coupon_code, subtotal, db)

    total_amount = round(subtotal + shipping_charges - discount_amount, 2)

    order = Order(
        order_number=generate_order_number(),
        customer_id=current_user.id,
        shipping_name=payload.shipping.name,
        shipping_phone=payload.shipping.phone,
        shipping_address=payload.shipping.address,
        shipping_city=payload.shipping.city,
        shipping_province=payload.shipping.province,
        subtotal=subtotal,
        shipping_charges=shipping_charges,
        discount_amount=discount_amount,
        total_amount=total_amount,
        payment_method="cod",
        payment_status="unpaid",
        status="pending",
        coupon_code=payload.coupon_code.upper() if payload.coupon_code else None,
        customer_note=payload.customer_note,
    )
    db.add(order)
    db.flush()

    for item in cart.items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product.name,
            product_image=item.product.image_url,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=round(item.unit_price * item.quantity, 2),
        ))
        item.product.stock -= item.quantity

    if coupon_obj:
        coupon_obj.used_count += 1

    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    db.refresh(order)
    return order


@router.get("/my", response_model=OrderListOut)
def my_orders(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(Order).filter(Order.customer_id == current_user.id).order_by(Order.created_at.desc())
    total = q.count()
    results = q.offset((page - 1) * page_size).limit(page_size).all()
    return OrderListOut(total=total, page=page, page_size=page_size, results=results)


@router.get("/my/{order_id}", response_model=OrderOut)
def get_my_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.customer_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("", response_model=OrderListOut)
def admin_list_orders(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status: Optional[str] = None, city: Optional[str] = None, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    q = db.query(Order).order_by(Order.created_at.desc())
    if status:
        q = q.filter(Order.status == status)
    if city:
        q = q.filter(Order.shipping_city.ilike(f"%{city}%"))
    total = q.count()
    results = q.offset((page - 1) * page_size).limit(page_size).all()
    return OrderListOut(total=total, page=page, page_size=page_size, results=results)


@router.get("/{order_id}", response_model=OrderOut)
def admin_get_order(order_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled", "refunded"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    order.status = payload.status
    if payload.admin_note:
        order.admin_note = payload.admin_note
    if payload.tracking_number:
        order.tracking_number = payload.tracking_number
    if payload.courier:
        order.courier = payload.courier
    if payload.status == "delivered":
        order.payment_status = "paid"
    db.commit()
    db.refresh(order)
    return order
