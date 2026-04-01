from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin Analytics"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == "pending").count()
    delivered_orders = db.query(Order).filter(Order.status == "delivered").count()
    total_revenue = db.query(func.sum(Order.total_amount)).filter(Order.status == "delivered").scalar() or 0.0
    total_customers = db.query(User).filter(User.is_admin == False).count()
    total_products = db.query(Product).filter(Product.is_active == True).count()
    low_stock = db.query(Product).filter(Product.stock <= 5, Product.is_active == True).count()

    top_products = (
        db.query(OrderItem.product_name, func.sum(OrderItem.quantity).label("units_sold"))
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
        .all()
    )

    recent_orders = (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "stats": {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "delivered_orders": delivered_orders,
            "total_revenue_pkr": round(total_revenue, 2),
            "total_customers": total_customers,
            "total_products": total_products,
            "low_stock_products": low_stock,
        },
        "top_products": [{"name": r[0], "units_sold": r[1]} for r in top_products],
        "recent_orders": [
            {
                "id": o.id,
                "order_number": o.order_number,
                "customer_id": o.customer_id,
                "total_amount": o.total_amount,
                "status": o.status,
                "city": o.shipping_city,
                "created_at": o.created_at,
            }
            for o in recent_orders
        ],
    }


@router.get("/customers")
def list_customers(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    customers = db.query(User).filter(User.is_admin == False).order_by(User.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "full_name": c.full_name,
            "email": c.email,
            "phone": c.phone,
            "is_active": c.is_active,
            "order_count": len(c.orders),
            "created_at": c.created_at,
        }
        for c in customers
    ]


@router.patch("/customers/{customer_id}/toggle")
def toggle_customer(customer_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    user = db.query(User).filter(User.id == customer_id, User.is_admin == False).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Customer not found")
    user.is_active = not user.is_active
    db.commit()
    return {"customer_id": customer_id, "is_active": user.is_active}
