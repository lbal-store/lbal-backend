from collections.abc import AsyncGenerator

from app.db.session import SessionLocal


async def get_db() -> AsyncGenerator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
