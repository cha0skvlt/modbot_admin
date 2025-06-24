import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
import os

import pytest

from modules import admin
from modules import db as db_module


class FakeFrom:
    def __init__(self, user_id):
        self.id = user_id


class FakeMessage:
    def __init__(self, text, user_id):
        self.text = text
        self.from_user = FakeFrom(user_id)
        self.responses: list[str] = []

    async def answer(self, text: str) -> None:
        self.responses.append(text)


def setup_env(tmp_path):
    os.environ["OWNER_ID"] = "1"

    class DummyDB:
        def __init__(self):
            self.admins = set()

        async def execute(self, query: str, *args):
            if query.startswith("CREATE TABLE"):
                return
            if query.startswith("INSERT"):
                self.admins.add(args[0])
            elif query.startswith("DELETE"):
                self.admins.discard(args[0])

        async def fetch(self, query: str, *args):
            return [{"user_id": uid} for uid in sorted(self.admins)]

    db_module.db = DummyDB()
    admin.db = db_module.db


@pytest.mark.asyncio
async def test_admin_commands(tmp_path):
    setup_env(tmp_path)
    await admin.startup()

    m = FakeMessage("/add_admin 2", 1)
    await admin.add_admin(m)
    assert m.responses[-1] == "Added admin 2"

    m = FakeMessage("/list_admin", 1)
    await admin.list_admin(m)
    assert m.responses[-1] == "2"

    m = FakeMessage("/rm_admin 2", 1)
    await admin.rm_admin(m)
    assert m.responses[-1] == "Removed admin 2"

    m = FakeMessage("/list_admin", 1)
    await admin.list_admin(m)
    assert m.responses[-1] == "No admins."
