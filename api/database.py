import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


def get_database_url() -> str:
    """
    Construye la URL de la base de datos según la configuración del .env
    Soporta SQLite y PostgreSQL
    """
    db_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
    
    if db_type == "sqlite":
        db_path = os.getenv("SQLITE_DB_PATH", "./data.db")
        return f"sqlite+aiosqlite:///{db_path}"
    
    elif db_type == "postgresql":
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "things_db")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
    
    else:
        raise ValueError(f"DATABASE_TYPE no soportado: {db_type}. Use 'sqlite' o 'postgresql'")


DATABASE_URL = get_database_url()
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite").lower()

engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
