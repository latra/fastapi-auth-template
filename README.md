# FastAPI Auth Template

FastAPI template with authentication and multi-database support.

## Setup

### 1. Install dependencies

This project uses `pyproject.toml` with optional dependencies for different databases.

#### Option A: With PostgreSQL (recommended for production)

```bash
uv sync --extra postgres
```

#### Option B: With SQLite (development/testing)

```bash
uv sync --extra sqlite
```

#### Option C: Everything (full development setup)

```bash
uv sync --extra dev
```

#### Without uv (using pip)

```bash
# With PostgreSQL
pip install -e ".[postgres]"

# With SQLite
pip install -e ".[sqlite]"

# Everything
pip install -e ".[dev]"
```

### 2. Configure environment variables

Copy the `.env.example` file to `.env` and adjust the values for your environment:

```bash
cp .env.example .env
```

### 3. Choose database

In the `.env` file, configure `DATABASE_TYPE`:

#### Option A: SQLite (default)

```env
DATABASE_TYPE=sqlite
SQLITE_DB_PATH=./data.db
```

#### Option B: PostgreSQL

```env
DATABASE_TYPE=postgresql
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=things_db
```

### 4. Run the application

```bash
# With uv (recommended)
uv run fastapi dev api/main.py

# Or with uvicorn directly
cd api
uvicorn main:app --reload
```

## Project structure

```
api/
├── main.py              # Application entry point
├── database.py          # Database configuration
├── auth.py              # Authentication utilities
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── dependencies.py      # FastAPI dependencies
├── routes/              # API endpoints
└── services/            # Business logic
```

## Environment variables

| Variable | Description | Default value |
|----------|-------------|---------------|
| `DATABASE_TYPE` | Database type: `sqlite` or `postgresql` | `sqlite` |
| `SQLITE_DB_PATH` | Path to SQLite file | `./data.db` |
| `POSTGRES_USER` | PostgreSQL user | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | PostgreSQL database name | `things_db` |
| `SECRET_KEY` | Secret key for JWT | `change-me-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration in minutes | `60` |
| `ALLOWED_ORIGINS` | Allowed CORS origins | `*` |
