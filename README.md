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

### 2. Configure the application

All configuration lives in `config.yaml`. Secrets are never written there directly: a value of the form `$NAME` is read from the environment variable `NAME` (or from `.env`, which is loaded automatically).

```yaml
app:
  name: "FastAPI Backend"

database:
  type: "postgresql"   # sqlite | postgresql
  host: "localhost"
  port: 5432
  database: "mydb"
  user: $POSTGRES_USER
  password: $POSTGRES_PASSWORD
  sqlite_path: "./data.db"

auth:
  secret_key: $SECRET_KEY
  access_token_expire_minutes: 60

cors:
  allowed_origins: $ALLOWED_ORIGINS   # comma-separated list or "*"
```

Rules:
- An environment variable is only read if `config.yaml` references it. Setting `SECRET_KEY` in the environment does nothing unless the yaml says `secret_key: $SECRET_KEY`.
- A referenced variable that is not set is a startup error, as are unknown keys and values of the wrong type.
- Values from the environment are converted to the field's type (`"5432"` → `5432`, `"true"` → `True`, `"a, b"` → `["a", "b"]`).
- Use `$$` for a literal value that starts with `$` (`$$abc` → `$abc`).

Create `.env` with the referenced values:

```bash
cp .env.sample .env
```

### 3. Google OAuth (optional)

First enable it in `config.yaml`:

```yaml
google:
  enabled: true
  client_id: $GOOGLE_CLIENT_ID
  client_secret: $GOOGLE_CLIENT_SECRET
  redirect_uri: $GOOGLE_REDIRECT_URI
  frontend_url: $FRONTEND_URL
```

When `enabled` is `false` or the section is absent, no Google-related endpoints are registered and none of the Google libraries are imported.

Then:

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services → Credentials → Create OAuth 2.0 Client ID**.
2. Set the application type to **Web application**.
3. Add the redirect URI (must match `google.redirect_uri`): `http://localhost:8000/auth/google/callback`.
4. Copy the client ID and secret into `.env`:

```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:5173
```

OAuth flow:
- `GET /auth/google/login` — sets a short-lived `state` cookie (CSRF protection) and redirects to Google's consent screen.
- `GET /auth/google/callback` — validates `state`, exchanges the code, creates the user and redirects to `<google.frontend_url>/#token=<jwt>`.

On any failure the callback redirects to `<google.frontend_url>/#error=<code>` instead, so the user always lands back on the frontend:

| Code | Meaning |
|---|---|
| `access_denied` | The user cancelled the Google consent screen |
| `invalid_state` | Missing/mismatched `state` (expired flow or CSRF attempt) |
| `missing_code` | Google returned no authorization code |
| `code_exchange_failed` | Google rejected the authorization code |
| `google_unavailable` | Could not reach Google |
| `invalid_id_token` | The ID token could not be verified |
| `email_not_verified` | The Google account's email is not verified |
| `account_exists` | The email belongs to an existing password account |

Google-only accounts are matched by Google ID or email. A password account with the same email is **not** linked automatically: otherwise whoever registered that email with a password would keep access to the Google user's account.

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
config.yaml              # Non-sensitive app configuration
.env                     # Secrets (not committed)
api/
├── main.py              # Application entry point
├── config.py            # Settings (loads config.yaml, resolves $ENV_VARS)
├── database.py          # Database engine setup
├── auth.py              # JWT utilities
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── dependencies.py      # FastAPI dependencies
├── routes/              # API endpoints
└── services/
    ├── auth_service.py         # Email/password logic
    └── google_auth_service.py  # Google OAuth logic
```

## Configuration reference

All keys go in `config.yaml`; any of them can be `$ENV_VAR`.

| Key | Description | Default |
|-----|-------------|---------|
| `app.name` | Application name | `FastAPI Backend` |
| `database.type` | `sqlite` or `postgresql` | `sqlite` |
| `database.host` / `port` / `database` | PostgreSQL connection info | `localhost` / `5432` / `postgres` |
| `database.user` / `password` | PostgreSQL credentials | — |
| `database.sqlite_path` | SQLite file path | `./data.db` |
| `auth.secret_key` | JWT signing key | **required** |
| `auth.access_token_expire_minutes` | JWT TTL | `60` |
| `auth.algorithm` | JWT algorithm | `HS256` |
| `cors.allowed_origins` | CORS origins (list, comma-separated string or `*`) | `*` |
| `google.enabled` | Enable Google OAuth endpoints | `false` |
| `google.client_id` / `client_secret` | Google OAuth credentials | required if enabled |
| `google.redirect_uri` | Google OAuth redirect URI | `http://localhost:8000/auth/google/callback` |
| `google.frontend_url` | Where the user is redirected after Google OAuth | `http://localhost:5173` |
