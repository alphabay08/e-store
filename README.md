# E-Store Backend API

FastAPI + PostgreSQL backend for a single-vendor e-commerce store (Pakistan focused).

## Tech Stack
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL (Render free tier)
- **Auth:** JWT via python-jose
- **ORM:** SQLAlchemy

## API Base URL
```
https://your-app.onrender.com/api/v1
```
Interactive docs available at `/docs` (Swagger UI)

---

## Deploy to Render (Free Tier) — Step by Step

### Option A: One-Click via render.yaml
1. Push this folder to a GitHub repository
2. Go to [render.com](https://render.com) → New → **Blueprint**
3. Connect your GitHub repo — Render reads `render.yaml` automatically
4. Click **Apply** — it creates the web service + free PostgreSQL DB together

### Option B: Manual
1. **Create PostgreSQL DB** → Render Dashboard → New → PostgreSQL → Free plan → Create
2. Copy the **Internal Database URL**
3. **Create Web Service** → New → Web Service → Connect your repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add **Environment Variables**:
   - `DATABASE_URL` = your PostgreSQL Internal URL
   - `SECRET_KEY` = any long random string
   - `ALGORITHM` = `HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES` = `10080`
5. Deploy!

### After First Deploy — Run Seed
In Render → your service → **Shell** tab:
```bash
python seed.py
```
This creates:
- Admin user: `admin@mystore.pk` / `Admin@123`
- 3 sample categories
- 3 sample products
- Coupon: `WELCOME10` (10% off)

---

## API Endpoints Summary

### Auth `/api/v1/auth`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | — | Register customer |
| POST | `/login` | — | Login, get JWT token |
| GET | `/me` | Customer | Get my profile |
| PUT | `/me` | Customer | Update my profile |

### Categories `/api/v1/categories`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `` | — | List all active categories |
| GET | `/{id}` | — | Get category by ID |
| GET | `/slug/{slug}` | — | Get category by slug |
| POST | `` | Admin | Create category |
| PUT | `/{id}` | Admin | Update category |
| DELETE | `/{id}` | Admin | Delete category |

### Products `/api/v1/products`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `` | — | List products (search, filter, paginate) |
| GET | `/featured` | — | Get featured products |
| GET | `/{id}` | — | Get product by ID |
| GET | `/slug/{slug}` | — | Get product by slug |
| POST | `` | Admin | Create product |
| PUT | `/{id}` | Admin | Update product |
| DELETE | `/{id}` | Admin | Soft-delete product |
| PATCH | `/{id}/stock` | Admin | Update stock |

### Cart `/api/v1/cart`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `` | Customer | View my cart |
| POST | `/items` | Customer | Add item to cart |
| PUT | `/items/{id}` | Customer | Update item quantity |
| DELETE | `/items/{id}` | Customer | Remove item |
| DELETE | `` | Customer | Clear entire cart |

### Orders `/api/v1/orders`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `` | Customer | Place order (COD) from cart |
| GET | `/my` | Customer | My order history |
| GET | `/my/{id}` | Customer | My order detail |
| GET | `` | Admin | All orders (filterable) |
| GET | `/{id}` | Admin | Order detail |
| PATCH | `/{id}/status` | Admin | Update order status |

### Coupons `/api/v1/coupons`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/validate` | Customer | Validate coupon code |
| GET | `` | Admin | List all coupons |
| POST | `` | Admin | Create coupon |
| DELETE | `/{id}` | Admin | Delete coupon |

### Admin `/api/v1/admin`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/dashboard` | Admin | Stats + top products + recent orders |
| GET | `/customers` | Admin | List all customers |
| PATCH | `/customers/{id}/toggle` | Admin | Enable/disable customer |

### Reviews `/api/v1/reviews`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/product/{id}` | — | Get reviews for product |
| POST | `` | Customer | Submit review |

---

## Authentication
All protected endpoints require:
```
Authorization: Bearer <your_jwt_token>
```
Get the token from `/api/v1/auth/login` response.

## Order Flow (COD)
1. Customer registers / logs in
2. Add products to cart → `POST /api/v1/cart/items`
3. (Optional) Validate coupon → `POST /api/v1/coupons/validate`
4. Place order → `POST /api/v1/orders` with shipping address + optional coupon
5. Admin views order at `/api/v1/orders`
6. Admin updates status → `PATCH /api/v1/orders/{id}/status`
   - Statuses: `pending → confirmed → processing → shipped → delivered`

## Shipping Charges (City-Based)
| City | Charge (PKR) |
|------|-------------|
| Karachi | 150 |
| Lahore | 200 |
| Islamabad | 200 |
| Rawalpindi | 200 |
| Other | 250 |

To change charges, edit `SHIPPING_CHARGES` dict in `app/routers/orders.py`.

---

## Local Development
```bash
# 1. Clone / unzip project
# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your local PostgreSQL URL

# 5. Run server
uvicorn app.main:app --reload

# 6. Seed data (optional)
python seed.py
```
Open http://localhost:8000/docs for Swagger UI.
