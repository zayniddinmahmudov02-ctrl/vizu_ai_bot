import asyncpg
from config import DATABASE_URL
from config import *
pool = None
# ==========================
# INITIALIZATION
# ==========================
async def init_db():

    global pool

    pool = await asyncpg.create_pool(
        DATABASE_URL
    )

    async with pool.acquire() as conn:

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id BIGINT PRIMARY KEY,
            full_name TEXT,
            bot_name TEXT DEFAULT 'vizu_homework',
            total_score INTEGER DEFAULT 0,
            accepted_tasks INTEGER DEFAULT 0,
            rejected_tasks INTEGER DEFAULT 0
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions(
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            full_name TEXT,
            lesson_number INTEGER,
            file_id TEXT,
            file_type TEXT,
            score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            teacher_comment TEXT                
            created_at TIMESTAMP DEFAULT NOW()
        )
        """)

        # Eski bazalarda bot_name bo'lmasa qo'shib qo'yadi
        await conn.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS bot_name TEXT
        """)
# ==========================
# USERS
# ==========================
async def add_user(
    user_id: int,
    full_name: str
):

    async with pool.acquire() as conn:

        await conn.execute(
            """
            INSERT INTO users(
                user_id,
                full_name,
                bot_name
            )
            VALUES($1,$2,$3)
            ON CONFLICT(user_id)
            DO NOTHING
            """,
            user_id,
            full_name,
            BOT_NAME
        )
    # ==========================
# ==========================
# SUBMISSIONS
# ==========================
async def add_submission(
    user_id,
    full_name,
    lesson_number,
    file_id,
    file_type
):

    async with pool.acquire() as conn:

        row = await conn.fetchrow(
            """
            INSERT INTO submissions(
                user_id,
                full_name,
                lesson_number,
                file_id,
                file_type
            )
            VALUES($1,$2,$3,$4,$5)
            RETURNING id
            """,
            user_id,
            full_name,
            lesson_number,
            file_id,
            file_type
        )

        return row["id"]


async def get_submission(
    submission_id
):

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            SELECT *
            FROM submissions
            WHERE id=$1
            """,
            submission_id
        )


async def update_score(
    submission_id,
    score,
    status
):

    async with pool.acquire() as conn:

        submission = await conn.fetchrow(
            """
            SELECT *
            FROM submissions
            WHERE id=$1
            """,
            submission_id
        )

        if not submission:
            return False

        if submission["status"] != "pending":
            return False

        user_id = submission["user_id"]

        await conn.execute(
            """
            UPDATE submissions
            SET score=$1,
                status=$2
            WHERE id=$3
            """,
            score,
            status,
            submission_id
        )

        if score >= 4:

            await conn.execute(
                """
                UPDATE users
                SET
                    total_score = total_score + $1,
                    accepted_tasks = accepted_tasks + 1
                WHERE user_id=$2
                """,
                score,
                user_id
            )

        else:

            await conn.execute(
                """
                UPDATE users
                SET
                    rejected_tasks = rejected_tasks + 1
                WHERE user_id=$1
                """,
                user_id
            )

        return True
# ==========================
# LESSON ALREADY PASSED
# ==========================

async def lesson_already_passed(
    user_id: int,
    lesson_number: int
):

    async with pool.acquire() as conn:

        row = await conn.fetchrow(
            """
            SELECT id
            FROM submissions
            WHERE user_id=$1
            AND lesson_number=$2
            AND status='accepted'
            LIMIT 1
            """,
            user_id,
            lesson_number
        )

        return row is not None
# ==========================
# GET USER
# ==========================
async def get_user(
    user_id: int
):

    async with pool.acquire() as conn:

        return await conn.fetchrow(
            """
            SELECT *
            FROM users
            WHERE user_id=$1
            AND bot_name=$2
            """,
            user_id,
            BOT_NAME
        )
# ==========================
# UPDATE NAME
# ==========================
async def update_name(
    user_id: int,
    new_name: str
):

    async with pool.acquire() as conn:

        await conn.execute(
            """
            UPDATE users
            SET full_name=$1
            WHERE user_id=$2
            AND bot_name=$3
            """,
            new_name,
            user_id,
            BOT_NAME
        )
# ==========================
# TOP USERS
# ==========================
async def get_top_users(
    limit=20
):

    async with pool.acquire() as conn:

        return await conn.fetch(
            """
            SELECT
                full_name,
                total_score
            FROM users
            WHERE bot_name=$1
            ORDER BY
                total_score DESC,
                accepted_tasks DESC
            LIMIT $2
            """,
            BOT_NAME,
            limit
        )
# ==========================
# RANKING
# ==========================
async def get_user_rank(
    user_id
):

    async with pool.acquire() as conn:

        rows = await conn.fetch(
            """
            SELECT user_id
            FROM users
            WHERE bot_name=$1
            ORDER BY
                total_score DESC,
                accepted_tasks DESC
            """,
            BOT_NAME
        )

        for i, row in enumerate(
            rows,
            start=1
        ):
            if row["user_id"] == user_id:
                return i

        return "-"
# ==========================
# USERS COUNT
# ==========================
async def get_users_count():

    async with pool.acquire() as conn:

        return await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM users
            WHERE bot_name=$1
            """,
            BOT_NAME
        )
# ==========================
# TASKS COUNT
# ==========================
async def get_tasks_count():

    async with pool.acquire() as conn:

        return await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM submissions
            """
        )