from collections.abc import Awaitable
from typing import Callable, ParamSpec, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Concatenate

from app.database.base import async_engine

# Определяем ParamSpec для параметров декорируемой функции (кроме session)
P = ParamSpec("P")
# Определяем TypeVar для типа возвращаемого значения декорируемой функции
R = TypeVar("R")


def connection(func: Callable[Concatenate[AsyncSession, P], Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """Декоратор возвращающий асинхронное подключение к БД."""
    async def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        async with AsyncSession(async_engine) as session, session.begin():
            return await func(session, *args, **kwargs)
    return inner
