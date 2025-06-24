from __future__ import annotations

import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

from modules.db import db

router = Router()


async def startup() -> None:
    load_dotenv()
    await db.execute("CREATE TABLE IF NOT EXISTS admins(user_id BIGINT PRIMARY KEY)")


def _owner_only(func):
    async def wrapper(message: Message, *args, **kwargs):
        owner_id = int(os.environ.get("OWNER_ID", 0))
        if message.from_user and message.from_user.id == owner_id:
            return await func(message, *args, **kwargs)
        await message.answer("🚫 Access denied.")
    return wrapper


@router.message(Command("add_admin"))
@_owner_only
async def add_admin(message: Message) -> None:
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Usage: /add_admin <user_id>")
        return
    uid = int(parts[1])
    await db.execute(
        "INSERT INTO admins(user_id) VALUES($1) ON CONFLICT DO NOTHING", uid
    )
    await message.answer(f"Added admin {uid}")


@router.message(Command("rm_admin"))
@_owner_only
async def rm_admin(message: Message) -> None:
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Usage: /rm_admin <user_id>")
        return
    uid = int(parts[1])
    await db.execute("DELETE FROM admins WHERE user_id=$1", uid)
    await message.answer(f"Removed admin {uid}")


@router.message(Command("list_admin"))
@_owner_only
async def list_admin(message: Message) -> None:
    rows = await db.fetch("SELECT user_id FROM admins")
    admins = [str(r["user_id"]) for r in rows]
    text = ", ".join(admins) if admins else "No admins."
    await message.answer(text)
