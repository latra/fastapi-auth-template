import os
from contextlib import asynccontextmanager

import fastapi
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()

from database import Base, engine, DATABASE_TYPE
from routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    async with engine.begin() as conn:
        if DATABASE_TYPE == "postgresql":
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        await conn.run_sync(Base.metadata.create_all)
        
        if DATABASE_TYPE == "postgresql":
            await conn.execute(text(
                "ALTER TABLE things ADD COLUMN IF NOT EXISTS meta_author VARCHAR(200) NOT NULL DEFAULT ''"
            ))
            await conn.execute(text(
                "ALTER TABLE things ADD COLUMN IF NOT EXISTS type VARCHAR(20) NOT NULL DEFAULT 'notes'"
            ))
    yield

app = fastapi.FastAPI(lifespan=lifespan)

# Configurar CORS desde variables de entorno
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
origins_list = [origin.strip() for origin in allowed_origins.split(",")] if allowed_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}
