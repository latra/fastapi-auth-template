from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email))


async def create(
    db: AsyncSession,
    *,
    name: str,
    email: str,
    hashed_password: str,
    profile_picture: str | None = None,
) -> User:
    user = User(
        name=name,
        email=email,
        hashed_password=hashed_password,
        profile_picture=profile_picture,
    )
    db.add(user)
    await db.flush()
    return user
