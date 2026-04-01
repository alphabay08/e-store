from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.routers import auth, categories, products, cart, orders, coupons, admin, reviews

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-Store API",
    description="Single-vendor e-commerce backend — Pakistan focused",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers under /api/v1
PREFIX = "/api/v1"
app.include_router(auth.router,       prefix=PREFIX)
app.include_router(categories.router, prefix=PREFIX)
app.include_router(products.router,   prefix=PREFIX)
app.include_router(cart.router,       prefix=PREFIX)
app.include_router(orders.router,     prefix=PREFIX)
app.include_router(coupons.router,    prefix=PREFIX)
app.include_router(admin.router,      prefix=PREFIX)
app.include_router(reviews.router,    prefix=PREFIX)


@app.get("/")
def root():
    return {"message": "E-Store API is running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
