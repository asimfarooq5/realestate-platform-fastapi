# Malkiyat Real Estate API - FastAPI Backend

A professional, async FastAPI backend for the Malkiyat real estate platform.

## Features

- **Async Support**: Fully async with SQLAlchemy 2.0 and asyncpg
- **JWT Authentication**: Secure token-based authentication with bcrypt hashing
- **CRUD Operations**: Full CRUD for properties, users, cities, areas
- **Search & Filter**: Advanced property search with multiple filters
- **Favorites**: Save and manage favorite properties
- **Admin Moderation**: Approve/reject listings, manage users and roles
- **Data Validation**: Pydantic schemas for request/response validation
- **Auto Documentation**: Interactive API docs at `/docs`

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (dev) / PostgreSQL (production, with asyncpg)
- **ORM**: SQLAlchemy 2.0 with async support
- **Migrations**: Alembic
- **Authentication**: JWT with python-jose, bcrypt via passlib
- **Deployment**: Docker + docker-compose

## Quick Start (Development)

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment — copy the example and fill in a real secret:
```bash
cp .env.example .env
# Generate a secret: openssl rand -hex 32
```

4. Create tables and seed data:
```bash
alembic upgrade head
python -m app.seed
```

5. Run the server:
```bash
python run.py   # or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. Open API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Default Seeded Accounts

| Role  | Email              | Password   |
|-------|--------------------|------------|
| Admin | admin@zameen.com   | admin123   |
| Agent | agent@zameen.com   | agent123   |

> Change these passwords immediately after first login.

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user (always BUYER role)
- `POST /api/v1/auth/login` - Login and get JWT token

### Properties
- `GET /api/v1/properties/` - List properties (with filters, pagination)
- `GET /api/v1/properties/{slug}` - Get property details
- `POST /api/v1/properties/` - Create new property (agent/seller/admin)
- `PUT /api/v1/properties/{id}` - Update property (owner/admin)
- `DELETE /api/v1/properties/{id}` - Delete property (owner/admin)
- `POST /api/v1/properties/{id}/inquiry` - Create inquiry (auth required)
- `POST /api/v1/properties/{id}/favorite` - Add to favorites
- `DELETE /api/v1/properties/{id}/favorite` - Remove from favorites
- `GET /api/v1/properties/{id}/favorite/status` - Check favorite status

### Cities & Areas
- `GET /api/v1/properties/cities/list` - List all cities
- `GET /api/v1/properties/cities/{id}/areas` - List areas in city

### User Account
- `GET /api/v1/users/me` - Current user profile
- `GET /api/v1/users/me/favorites` - My favorite properties
- `GET /api/v1/users/me/inquiries` - My inquiries
- `GET /api/v1/users/me/properties` - My listed properties

### Admin (ADMIN role only)
- `GET /api/v1/admin/properties` - All properties (filter by status)
- `PUT /api/v1/admin/properties/{id}/moderation` - Approve/reject/feature
- `GET /api/v1/admin/inquiries` - All inquiries
- `GET /api/v1/admin/users` - All users
- `PUT /api/v1/admin/users/{id}/role` - Change user role

## Environment Variables

See `.env.example`. Required:
- `SECRET_KEY` — **required**, minimum 32 chars (`openssl rand -hex 32`)
- `DATABASE_URL` — SQLite for dev, PostgreSQL for production
- `BACKEND_CORS_ORIGINS` — JSON array of allowed origins

## Production Deployment (Docker)

1. On your VPS, create `.env`:
```bash
cp .env.example .env
# Set SECRET_KEY, DATABASE_URL (postgresql+asyncpg://...), CORS
```

2. Build and start:
```bash
docker compose up -d --build
```

3. Run migrations and seed:
```bash
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.seed
```

4. Verify:
```bash
curl http://localhost:8000/health
```

5. Put a reverse proxy (Caddy/Nginx) in front for HTTPS.

## Database Models

- **User**: Buyers, sellers, agents, admins (roles, is_active)
- **Property**: Property listings with full details
- **City/Area**: Location data (10 Pakistani cities, 200 areas seeded)
- **PropertyImage**: Property photos
- **Favorite**: User's saved properties
- **Inquiry**: Contact requests
- **AgentProfile**: Agent details

## Migrations

```bash
alembic revision --autogenerate -m "description"   # create new migration
alembic upgrade head                                 # apply migrations
alembic downgrade -1                                 # rollback one step
```
