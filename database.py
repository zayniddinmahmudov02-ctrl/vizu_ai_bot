import asyncpg
from config import DATABASE_URL, BOT_NAME
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

        # USERS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users(
                user_id BIGINT PRIMARY KEY,
                full_name TEXT,
                bot_name TEXT DEFAULT '',
                total_score INTEGER DEFAULT 0,
                accepted_tasks INTEGER DEFAULT 0,
                rejected_tasks INTEGER DEFAULT 0
            )
        """)

        # SUBMISSIONS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions(
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                full_name TEXT,
                lesson_number INTEGER,
                file_id TEXT,
                file_type TEXT,

                channel_message_id BIGINT,

                score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # OLD DATABASE FIXES
        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS bot_name TEXT DEFAULT 'vizu_homework'
        """)

        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS total_score INTEGER DEFAULT 0
        """)

        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS accepted_tasks INTEGER DEFAULT 0
        """)

        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS rejected_tasks INTEGER DEFAULT 0
        """)

        await conn.execute("""
            ALTER TABLE submissions
            ADD COLUMN IF NOT EXISTS channel_message_id BIGINT
        """)

        # HOMEWORK USERS
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS homework_users(
                user_id BIGINT PRIMARY KEY,
                full_name TEXT,
                total_score INTEGER DEFAULT 0,
                accepted_tasks INTEGER DEFAULT 0,
                rejected_tasks INTEGER DEFAULT 0
            )
        """)
# ==========================
# SUBMISSIONS TABLE FIX
# ==========================
async def init_db():
    global pool

    pool = await asyncpg.create_pool(
        DATABASE_URL
    )

    async with pool.acquire() as conn:

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions(
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                full_name TEXT,
                lesson_number INTEGER,
                file_id TEXT,
                file_type TEXT,

                channel_message_id BIGINT,

                score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        await conn.execute("""
            ALTER TABLE submissions
            ADD COLUMN IF NOT EXISTS channel_message_id BIGINT
        """)
# ==========================
# ADD SUBMISSION
# ==========================
async def add_submission(
    user_id,
    full_name,
    lesson_number,
    task_number,
    file_id,
    file_type
):
    async with pool.acquire() as conn:

        row = await conn.fetchrow("""
            INSERT INTO submissions(
                user_id,
                full_name,
                lesson_number,
                task_number,
                file_id,
                file_type
            )
            VALUES($1,$2,$3,$4,$5,$6)
            RETURNING id
        """,
            user_id,
            full_name,
            lesson_number,
            task_number,
            file_id,
            file_type
        )

        return row["id"]


# ==========================
# SAVE CHANNEL MESSAGE ID
# ==========================
async def save_channel_message_id(
    submission_id,
    channel_message_id
):
    async with pool.acquire() as conn:

        await conn.execute("""
            UPDATE submissions
            SET channel_message_id=$1
            WHERE id=$2
        """,
            channel_message_id,
            submission_id
        )

# ==========================
# GET SUBMISSION
# ==========================
async def get_submission(
    submission_id
):
    async with pool.acquire() as conn:

        return await conn.fetchrow("""
            SELECT *
            FROM submissions
            WHERE id=$1
        """,
            submission_id
        )
# ==========================
# UPDATE SCORE
# ==========================
async def update_score(
    submission_id,
    score,
    status
):
    async with pool.acquire() as conn:

        print(f"UPDATE SCORE START: {submission_id}")

        submission = await conn.fetchrow("""
            SELECT *
            FROM submissions
            WHERE id=$1
        """, submission_id)

        print(f"SUBMISSION: {submission}")

        if not submission:
            print("SUBMISSION NOT FOUND")
            return False

        print(f"STATUS BEFORE: {submission['status']}")

        if submission["status"] != "pending":
            print("ALREADY CHECKED")
            return False

        user_id = submission["user_id"]

        print(f"USER ID: {user_id}")
        print(f"SCORE: {score}")

        await conn.execute("""
            INSERT INTO homework_users(
                user_id,
                full_name
            )
            VALUES($1,$2)
            ON CONFLICT(user_id)
            DO NOTHING
        """,
            submission["user_id"],
            submission["full_name"]
        )

        await conn.execute("""
            UPDATE submissions
            SET
                score=$1,
                status=$2
            WHERE id=$3
        """,
            score,
            status,
            submission_id
        )

        if score >= 4:

            await conn.execute("""
                UPDATE homework_users
                SET
                    total_score = total_score + $1,
                    accepted_tasks = accepted_tasks + 1
                WHERE user_id=$2
            """,
                score,
                user_id
            )

            print("ACCEPTED TASK UPDATED")

        else:

            await conn.execute("""
                UPDATE homework_users
                SET
                    rejected_tasks = rejected_tasks + 1
                WHERE user_id=$1
            """,
                user_id
            )

            print("REJECTED TASK UPDATED")

        print("UPDATE SCORE SUCCESS")

        return True
# ==========================
# SAVE CHANNEL MESSAGE ID
# ==========================
async def save_channel_message_id(
    submission_id,
    channel_message_id
):
    async with pool.acquire() as conn:

        await conn.execute("""
            UPDATE submissions
            SET channel_message_id=$1
            WHERE id=$2
        """,
            channel_message_id,
            submission_id
        )
# ==========================
# USERS
# ==========================
async def add_user(user_id: int, full_name: str):
    async with pool.acquire() as conn:

        await conn.execute("""
            INSERT INTO homework_users(
                user_id,
                full_name
            )
            VALUES($1,$2)
            ON CONFLICT(user_id)
            DO NOTHING
        """, user_id, full_name)
# ==========================
# LESSON ALREADY PASSED
# ==========================
async def lesson_already_passed(user_id: int, lesson_number: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id FROM submissions
            WHERE user_id=$1
            AND lesson_number=$2
            AND status='accepted'
            LIMIT 1
        """, user_id, lesson_number)
        return row is not None
# ==========================
# GET USER
# ==========================
async def get_user(user_id: int):
    async with pool.acquire() as conn:

        return await conn.fetchrow("""
            SELECT *
            FROM homework_users
            WHERE user_id=$1
        """, user_id)
# ==========================
# UPDATE NAME
# ==========================
async def update_name(user_id: int, new_name: str):
    async with pool.acquire() as conn:

        await conn.execute("""
            UPDATE homework_users
            SET full_name=$1
            WHERE user_id=$2
        """, new_name, user_id)
# =========================
# TOP USERS
# =========================
async def get_top_users(limit=100):
    async with pool.acquire() as conn:

        rows = await conn.fetch("""
            SELECT
                user_id,
                full_name,
                total_score,
                accepted_tasks
            FROM homework_users
            WHERE total_score > 0
            ORDER BY
                total_score DESC,
                accepted_tasks DESC
            LIMIT $1
        """, limit)

        print("TOP USERS:")
        print(rows)

        return rows
    
# ==========================
# RANKING
# ==========================
async def get_user_rank(user_id):
    async with pool.acquire() as conn:

        rows = await conn.fetch("""
            SELECT user_id
            FROM homework_users
            ORDER BY
                total_score DESC,
                accepted_tasks DESC
        """)

        for i, row in enumerate(rows, start=1):
            if row["user_id"] == user_id:
                return i

        return "-"
# ==========================
# USERS COUNT
# ==========================
async def get_users_count():
    async with pool.acquire() as conn:

        return await conn.fetchval("""
            SELECT COUNT(*)
            FROM homework_users
        """)
# ==========================
# TASKS COUNT
# ==========================
async def get_tasks_count():
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM submissions")