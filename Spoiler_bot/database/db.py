
import aiosqlite
from config import DB_PATH

async def init_db():
    """ایجاد جداول دیتابیس در صورت عدم وجود"""
    async with aiosqlite.connect(DB_PATH) as db:
        # جدول اصلی ذخیره اسپویل‌ها
        await db.execute("""
            CREATE TABLE IF NOT EXISTS spoilers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                username TEXT,
                title TEXT,
                spoiler_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                warning_message_id INTEGER
            )
        """)
        
        # جدول بازدیدها برای ثبت بازدیدهای یکتا
        await db.execute("""
            CREATE TABLE IF NOT EXISTS spoiler_views (
                spoiler_id INTEGER,
                user_id INTEGER,
                PRIMARY KEY (spoiler_id, user_id)
            )
        """)
        
        # جدول رتبه‌بندی کاربران
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                spoiler_count INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def add_spoiler(chat_id: int, user_id: int, username: str, title: str, spoiler_text: str) -> int:
    """افزودن اسپویلر جدید و افزایش آمار کاربر ارسال‌کننده"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO spoilers (chat_id, user_id, username, title, spoiler_text) VALUES (?, ?, ?, ?, ?)",
            (chat_id, user_id, username, title, spoiler_text)
        )
        spoiler_id = cursor.lastrowid
        
        # به‌روزرسانی یا ایجاد آمار کاربر
        await db.execute("""
            INSERT INTO user_stats (user_id, username, spoiler_count)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                username = excluded.username,
                spoiler_count = spoiler_count + 1
        """, (user_id, username))
        
        await db.commit()
        return spoiler_id

async def update_warning_message_id(spoiler_id: int, message_id: int):
    """ثبت شناسه پیام هشدار فرستاده شده در گروه"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE spoilers SET warning_message_id = ? WHERE id = ?",
            (message_id, spoiler_id)
        )
        await db.commit()

async def add_view_if_unique(spoiler_id: int, user_id: int) -> bool:
    """ثبت بازدید کاربر؛ اگر بازدید جدید باشد True برمی‌گرداند"""
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO spoiler_views (spoiler_id, user_id) VALUES (?, ?)",
                (spoiler_id, user_id)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

async def get_view_count(spoiler_id: int) -> int:
    """دریافت تعداد کل بازدیدهای یکتای یک اسپویلر"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM spoiler_views WHERE spoiler_id = ?",
            (spoiler_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0

async def get_top_spoilers(limit: int = 10):
    """دریافت آمار برترین ارسال‌کنندگان اسپویلر"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT username, spoiler_count FROM user_stats ORDER BY spoiler_count DESC LIMIT ?",
            (limit,)
        ) as cursor:
            return await cursor.fetchall()
            