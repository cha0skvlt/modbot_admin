from __future__ import annotations

import os
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
import yaml
import aiosqlite
import asyncpg

router = Router()

_DB_TYPE = None


def _get_db_type() -> str:
    global _DB_TYPE
    if _DB_TYPE is None:
        db_type = os.getenv("DB_TYPE")
        if not db_type and Path("config.yaml").exists():
            with open("config.yaml", "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                db_type = data.get("DB_TYPE")
        _DB_TYPE = (db_type or "sqlite").lower()
    return _DB_TYPE


async def _connect():
    db_type = _get_db_type()
    if db_type == "postgres":
        dsn = os.getenv("DATABASE_URL", "")
        return await asyncpg.connect(dsn=dsn)
    path = os.getenv("DATABASE_PATH", "database.db")
    return await aiosqlite.connect(path)


async def startup() -> None:
    load_dotenv()
    conn = await _connect()
    db_type = _get_db_type()
    if db_type == "postgres":
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS admins(user_id BIGINT PRIMARY KEY)"
        )
        await conn.close()
    else:
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS admins(user_id INTEGER PRIMARY KEY)"
        )
        await conn.commit()
        await conn.close()


def _owner_only(func):
    async def wrapper(message: Message, *args, **kwargs):
        owner_id = int(os.environ.get("OWNER_ID", 0))
        if message.from_user and message.from_user.id == owner_id:
            return await func(message, *args, **kwargs)
        await message.answer("\ud83d\udeab Access denied.")

    return wrapper


@router.message(Command("add_admin"))
@_owner_only
async def add_admin(message: Message) -> None:
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Usage: /add_admin <user_id>")
        return
    uid = int(parts[1])
    conn = await _connect()
    db_type = _get_db_type()
    if db_type == "postgres":
        await conn.execute(
            "INSERT INTO admins(user_id) VALUES($1) ON CONFLICT DO NOTHING", uid
        )
        await conn.close()
    else:
        await conn.execute("INSERT OR IGNORE INTO admins(user_id) VALUES (?)", (uid,))
        await conn.commit()
        await conn.close()
    await message.answer(f"Added admin {uid}")


@router.message(Command("rm_admin"))
@_owner_only
async def rm_admin(message: Message) -> None:
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Usage: /rm_admin <user_id>")
        return
    uid = int(parts[1])
    conn = await _connect()
    db_type = _get_db_type()
    if db_type == "postgres":
        await conn.execute("DELETE FROM admins WHERE user_id=$1", uid)
        await conn.close()
    else:
        await conn.execute("DELETE FROM admins WHERE user_id=?", (uid,))
        await conn.commit()
        await conn.close()
    await message.answer(f"Removed admin {uid}")


@router.message(Command("list_admin"))
@_owner_only
async def list_admin(message: Message) -> None:
    conn = await _connect()
    db_type = _get_db_type()
    if db_type == "postgres":
        rows = await conn.fetch("SELECT user_id FROM admins")
        admins = [str(r["user_id"]) for r in rows]
        await conn.close()
    else:
        cursor = await conn.execute("SELECT user_id FROM admins")
        rows = await cursor.fetchall()
        admins = [str(r[0]) for r in rows]
        await conn.close()
    text = ", ".join(admins) if admins else "No admins."
    await message.answer(text)
