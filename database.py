import aiosqlite

DB = "tasks.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            total_score INTEGER DEFAULT 0,
            accepted_tasks INTEGER DEFAULT 0,
            rejected_tasks INTEGER DEFAULT 0
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS submissions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            lesson_number INTEGER,
            file_id TEXT,
            file_type TEXT,
            score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        await db.commit()

# --- USERS ---
async def add_user(user_id: int, full_name: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("INSERT OR IGNORE INTO users(user_id, full_name) VALUES (?,?)", (user_id, full_name))
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return await cur.fetchone()

async def update_name(user_id: int, new_name: str):
    async with aiosqlite.connect(DB) as db:
        await db.execute("UPDATE users SET full_name=? WHERE user_id=?", (new_name, user_id))
        await db.commit()

async def get_top_users(limit=20):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT full_name, total_score FROM users ORDER BY total_score DESC, accepted_tasks DESC LIMIT ?", (limit,))
        return await cur.fetchall()

# --- SUBMISSIONS ---
async def add_submission(user_id, full_name, lesson_number, file_id, file_type):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("""
        INSERT INTO submissions(user_id, full_name, lesson_number, file_id, file_type) 
        VALUES(?,?,?,?,?)""", (user_id, full_name, lesson_number, file_id, file_type))
        await db.commit()
        return cur.lastrowid

async def get_submission(submission_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT * FROM submissions WHERE id=?", (submission_id,))
        return await cur.fetchone()

async def update_score(submission_id, score, status):
    async with aiosqlite.connect(DB) as db:
        # Prevent double grading by checking status
        cur = await db.execute("SELECT status FROM submissions WHERE id=?", (submission_id,))
        row = await cur.fetchone()
        if not row or row[0] != 'pending':
            return False
        
        await db.execute("UPDATE submissions SET score=?, status=? WHERE id=?", (score, status, submission_id))
        
        submission = await get_submission(submission_id)
        if submission:
            user_id = submission[1]
            if score >= 4:
                await db.execute("UPDATE users SET total_score = total_score + ?, accepted_tasks = accepted_tasks + 1 WHERE user_id=?", (score, user_id))
            else:
                await db.execute("UPDATE users SET rejected_tasks = rejected_tasks + 1 WHERE user_id=?", (user_id,))
        await db.commit()
        return True

async def get_user_rank(user_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT user_id FROM users ORDER BY total_score DESC, accepted_tasks DESC")
        rows = await cur.fetchall()
        for i, row in enumerate(rows, 1):
            if row[0] == user_id: return i
        return "-"