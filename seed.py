"""
Run this once after deployment to create the admin user and sample data.
Usage: python seed.py
"""
import os
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models.user import User
from app.models.product import Category, Product
from app.models.coupon import Coupon

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ── Admin user ────────────────────────────────────────────
existing_admin = db.query(User).filter(User.email == "admin@mystore.pk").first()
if not existing_admin:
    admin = User(
        full_name="Store Admin",
        email="admin@mystore.pk",
        phone="03001234567",
        hashed_password=hash_password("Admin@123"),
        is_admin=True,
    )
    db.add(admin)
    print("✅ Admin created: admin@mystore.pk / Admin@123")
else:
    print("ℹ️  Admin already exists")

# ── Sample categories ─────────────────────────────────────
cats = [
    {"name": "Electronics", "slug": "electronics", "description": "Gadgets and devices"},
    {"name": "Clothing",    "slug": "clothing",     "description": "Men and women apparel"},
    {"name": "Home & Kitchen", "slug": "home-kitchen", "description": "Home essentials"},
]
for c in cats:
    if not db.query(Category).filter(Category.slug == c["slug"]).first():
        db.add(Category(**c))
        print(f"✅ Category: {c['name']}")

db.commit()

# ── Sample products ───────────────────────────────────────
elec = db.query(Category).filter(Category.slug == "electronics").first()
sample_products = [
    {"name": "Wireless Earbuds", "slug": "wireless-earbuds", "price": 2500, "sale_price": 1999, "stock": 50, "is_featured": True, "category_id": elec.id if elec else None},
    {"name": "USB-C Charger", "slug": "usb-c-charger", "price": 800, "stock": 100, "category_id": elec.id if elec else None},
    {"name": "Phone Stand", "slug": "phone-stand", "price": 500, "stock": 75, "is_featured": True, "category_id": elec.id if elec else None},
]
for p in sample_products:
    if not db.query(Product).filter(Product.slug == p["slug"]).first():
        db.add(Product(**p))
        print(f"✅ Product: {p['name']}")

# ── Sample coupon ─────────────────────────────────────────
if not db.query(Coupon).filter(Coupon.code == "WELCOME10").first():
    db.add(Coupon(code="WELCOME10", discount_type="percent", discount_value=10, min_order_amount=500))
    print("✅ Coupon: WELCOME10 (10% off)")

db.commit()
db.close()
print("\n🎉 Seed complete!")
