from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.order import Review, Order, OrderItem
from app.models.user import User

router = APIRouter(prefix="/reviews", tags=["Reviews"])


class ReviewCreate(BaseModel):
    product_id: int
    rating: int
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    product_id: int
    customer_id: int
    rating: int
    comment: Optional[str]

    class Config:
        from_attributes = True


@router.get("/product/{product_id}", response_model=List[ReviewOut])
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.product_id == product_id).all()


@router.post("", response_model=ReviewOut, status_code=201)
def add_review(payload: ReviewCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not (1 <= payload.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    # Check if user already reviewed this product
    existing = db.query(Review).filter(Review.product_id == payload.product_id, Review.customer_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this product")

    review = Review(product_id=payload.product_id, customer_id=current_user.id, rating=payload.rating, comment=payload.comment)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
