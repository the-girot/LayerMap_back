from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException


@asynccontextmanager
async def handle_integrity(
    db: AsyncSession,
    detail: str = "Запись с таким именем уже существует"
):
    try:
        yield
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail=detail)