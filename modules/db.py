from __future__ import annotations

import os
import asyncpg


class Database:
    def __init__(self) -> None:
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self.pool is None:
            dsn = os.getenv("DATABASE_URL", "")
            self.pool = await asyncpg.create_pool(dsn=dsn)

    async def execute(self, query: str, *args) -> None:
        await self.connect()
        assert self.pool
        async with self.pool.acquire() as conn:
            await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        await self.connect()
        assert self.pool
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None


db = Database()
