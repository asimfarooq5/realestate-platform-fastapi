# Zameen Real Estate API - FastAPI Backend

A professional, async FastAPI backend for the Zameen real estate platform.

## Features

- **Async Support**: Fully async with SQLAlchemy 2.0 and asyncpg
- **JWT Authentication**: Secure token-based authentication
- **CRUD Operations**: Full CRUD for properties, users, cities, areas
- **Search & Filter**: Advanced property search with multiple filters
- **Data Validation**: Pydantic schemas for request/response validation
- **Auto Documentation**: Interactive API docs at `/docs`

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite (async) / PostgreSQL (with asyncpg)
- **ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT with python-jose
- **Password Hashing**: bcrypt via passlib

## Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python run.py
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. Open API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token

### Properties
- `GET /api/v1/properties/` - List properties (with filters)
- `GET /api/v1/properties/{slug}` - Get property details
- `POST /api/v1/properties/` - Create new property (auth required)
- `PUT /api/v1/properties/{id}` - Update property (auth required)
- `DELETE /api/v1/properties/{id}` - Delete property (auth required)
- `POST /api/v1/properties/{id}/inquiry` - Create inquiry (auth required)

### Cities & Areas
- `GET /api/v1/properties/cities/list` - List all cities
- `GET /api/v1/properties/cities/{id}/areas` - List areas in city

## Environment Variables

Create a `.env` file:

```env
DATABASE_URL=sqlite+aiosqlite:///./zameen.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Database Models

- **User**: Buyers, sellers, agents, admins
- **Property**: Property listings with full details
- **City/Area**: Location data
- **PropertyImage**: Property photos
- **Favorite**: User's saved properties
- **Inquiry**: Contact requests

## Testing

Run tests with pytest:
```bash
pytest
```

## Docker

Build and run with Docker:
```bash
docker build -t zameen-api .
docker run -p 8000:8000 zameen-api
```
# realestate-platform-fastapi
