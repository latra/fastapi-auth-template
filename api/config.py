"""Application settings, loaded only from config.yaml.

Any string value of the form ``$NAME`` is replaced by the environment variable
``NAME`` (loaded from .env if present). Environment variables are never read
unless config.yaml references them, and a referenced variable that is not set
is an error. Use ``$$`` to write a literal value starting with ``$``.
"""

import dataclasses
import os
import re
import typing
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
_ENV_REF = re.compile(r"^\$([A-Za-z_][A-Za-z0-9_]*)$")


class ConfigError(Exception):
    pass


@dataclass
class AppConfig:
    name: str = "FastAPI Backend"


@dataclass
class DatabaseConfig:
    type: str = "sqlite"
    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    user: str = ""
    password: str = ""
    sqlite_path: str = "./data.db"

    def url(self) -> str:
        if self.type == "sqlite":
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        if self.type == "postgresql":
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        raise ValueError(f"Unsupported database type: {self.type!r}. Use 'sqlite' or 'postgresql'.")


@dataclass
class AuthConfig:
    secret_key: str
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"


@dataclass
class GoogleOAuthConfig:
    enabled: bool = False
    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "http://localhost:8000/auth/google/callback"
    # Where the user is sent back after the OAuth flow (with #token=... or #error=...)
    frontend_url: str = "http://localhost:5173"


@dataclass
class CorsConfig:
    allowed_origins: list[str] = field(default_factory=lambda: ["*"])


@dataclass
class Settings:
    auth: AuthConfig
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    google: GoogleOAuthConfig = field(default_factory=GoogleOAuthConfig)
    cors: CorsConfig = field(default_factory=CorsConfig)

    @classmethod
    def load(cls, path: Path = _CONFIG_PATH) -> "Settings":
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        settings = _build(cls, _resolve_env(raw, "config"), "config")
        settings._validate()
        return settings

    def _validate(self) -> None:
        if not self.auth.secret_key:
            raise ConfigError("auth.secret_key must not be empty")
        if self.google.enabled and not (self.google.client_id and self.google.client_secret):
            raise ConfigError("google.client_id and google.client_secret are required when google.enabled is true")


def _resolve_env(value, where: str):
    if isinstance(value, dict):
        return {k: _resolve_env(v, f"{where}.{k}") for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v, f"{where}[{i}]") for i, v in enumerate(value)]
    if isinstance(value, str):
        if value.startswith("$$"):
            return value[1:]
        if match := _ENV_REF.match(value):
            name = match.group(1)
            if name not in os.environ:
                raise ConfigError(f"{where} references environment variable {name}, which is not set")
            return os.environ[name]
    return value


def _build(cls, raw, where: str):
    if not isinstance(raw, dict):
        raise ConfigError(f"{where} must be a mapping")
    hints = typing.get_type_hints(cls)
    fields = {f.name for f in dataclasses.fields(cls)}
    unknown = set(raw) - fields
    if unknown:
        raise ConfigError(f"Unknown keys in {where}: {', '.join(sorted(unknown))}")

    kwargs = {}
    for name, value in raw.items():
        kwargs[name] = _coerce(value, hints[name], f"{where}.{name}")
    try:
        return cls(**kwargs)
    except TypeError:
        missing = [
            f.name for f in dataclasses.fields(cls)
            if f.name not in kwargs
            and f.default is dataclasses.MISSING
            and f.default_factory is dataclasses.MISSING
        ]
        raise ConfigError(f"Missing required keys in {where}: {', '.join(missing)}") from None


def _coerce(value, hint, where: str):
    """Convert YAML values (or env var strings) to the field's declared type."""
    if dataclasses.is_dataclass(hint):
        return _build(hint, value, where)
    try:
        if hint is bool:
            if isinstance(value, str):
                if value.strip().lower() in ("true", "1", "yes", "on"):
                    return True
                if value.strip().lower() in ("false", "0", "no", "off", ""):
                    return False
                raise ValueError(value)
            return bool(value)
        if hint is int:
            return int(value)
        if hint is str:
            return str(value)
        if typing.get_origin(hint) is list:
            # Env vars arrive as strings: "a, b, c" -> ["a", "b", "c"]
            if isinstance(value, str):
                value = [v.strip() for v in value.split(",") if v.strip()]
            return [str(v) for v in value]
    except (TypeError, ValueError):
        raise ConfigError(f"Invalid value for {where}: {value!r}") from None
    return value


settings = Settings.load()
