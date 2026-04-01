from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartOut, CartItemOut

router = APIRouter(prefix="/cart", tags=["Cart"])


def get_or_create_cart(user: User, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.customer_id == user.id).first()
    if not cart:
        cart = Cart(customer_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def build_cart_out(cart: Cart) -> CartOut:
    items_out = []
    subtotal = 0.0
    for item in cart.items:
        total = round(item.unit_price * item.quantity, 2)
        subtotal += total
        items_out.append(CartItemOut(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=total,
            product=item.product,
        ))
    return CartOut(
        id=cart.id,
        customer_id=cart.customer_id,
        items=items_out,
        subtotal=round(subtotal, 2),
        item_count=len(items_out),
    )


@router.get("", response_model=CartOut)
def get_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = get_or_create_cart(current_user, db)
    return build_cart_out(cart)


@router.post("/items", response_model=CartOut, status_code=201)
def add_item(payload: CartItemAdd, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == payload.product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < payload.quantity:
        raise HTTPException(status_code=400, detail=f"Only {product.stock} items in stock")

    cart = get_or_create_cart(current_user, db)

    # Check if item already in cart
    existing = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == payload.product_id).first()
    if existing:
        new_qty = existing.quantity + payload.quantity
        if product.stock < new_qty:
            raise HTTPException(status_code=400, detail=f"Only {product.stock} items in stock")
        existing.quantity = new_qty
    else:
        price = product.sale_price if product.sale_price else product.price
        item = CartItem(cart_id=cart.id, product_id=payload.product_id, quantity=payload.quantity, unit_price=price)
        db.add(item)

    db.commit()
    db.refresh(cart)
    return build_cart_out(cart)


@router.put("/items/{item_id}", response_model=CartOut)
def update_item(item_id: int, payload: CartItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = get_or_create_cart(current_user, db)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    if payload.quantity <= 0:
        db.delete(item)
    else:
        if item.product.stock < payload.quantity:
            raise HTTPException(status_code=400, detail=f"Only {item.product.stock} in stock")
        item.quantity = payload.quantity

    db.commit()
    db.refresh(cart)
    return build_cart_out(cart)


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = get_or_create_cart(current_user, db)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return build_cart_out(cart)


@router.delete("", status_code=204)
def clear_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cart = db.query(Cart).filter(Cart.customer_id == current_user.id).first()
    if cart:
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.commit()
