# bot/db.py

import aiosqlite
from .config import DB_NAME
from datetime import datetime


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # состояние текущего квиза
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_state (
                user_id INTEGER PRIMARY KEY,
                question_index INTEGER,
                score INTEGER
            )
            """
        )
        # последние результаты
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_results (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                score INTEGER,
                total INTEGER,
                updated_at TEXT
            )
            """
        )
        await db.commit()


# ------- работа с состоянием квиза -------

async def set_quiz_state(user_id: int, question_index: int, score: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO quiz_state (user_id, question_index, score)
            VALUES (?, ?, ?)
            """,
            (user_id, question_index, score),
        )
        await db.commit()


async def get_quiz_state(user_id: int) -> tuple[int, int]:
    """Возвращает (question_index, score). Если нет записи — (0, 0)."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT question_index, score FROM quiz_state WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0], row[1]
            return 0, 0


async def reset_quiz_state(user_id: int):
    await set_quiz_state(user_id, 0, 0)


# ------- работа с результатами -------

async def save_quiz_result(user_id: int, username: str, score: int, total: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO quiz_results (user_id, username, score, total, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, username, score, total, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def get_user_result(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT username, score, total, updated_at FROM quiz_results WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            return await cursor.fetchone()


async def get_top_results(limit: int = 5):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            """
            SELECT username, score, total, updated_at
            FROM quiz_results
            ORDER BY score DESC, updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ) as cursor:
            return await cursor.fetchall()
