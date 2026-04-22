from contextlib import asynccontextmanager

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def handle_integrity(
    db: AsyncSession, detail: str = "Запись с таким именем уже существует"
):
    try:
        yield
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=409, detail=detail) from err
