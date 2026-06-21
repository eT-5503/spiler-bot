import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from database.db import init_db
from handlers.spoiler import handle_sp, handle_spoiler_click
from handlers.leaderboard import handle_top_spoilers

# تنظیم ساختار لاگر برای مانیتورینگ دقیق
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application):
    """راه‌اندازی اولیه و ساخت دیتابیس قبل از آنلاین شدن ربات"""
    logger.info("Initializing SQLite database...")
    await init_db()
    logger.info("Database synchronized successfully.")

def main():
    """نقطه ورود اصلی به برنامه"""
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Error: Please specify your BOT_TOKEN in config.py!")
        return

    # ساخت کلاینت اصلی با استفاده از توکن
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # ثبت تمامی دستورات متنی
    application.add_handler(CommandHandler("sp", handle_sp))
    application.add_handler(CommandHandler("topspoilers", handle_top_spoilers))

    # ثبت ردیاب دکمه‌های شیشه‌ای
    application.add_handler(CallbackQueryHandler(handle_spoiler_click, pattern="^show_"))

    # اجرای دائمی ربات به روش غیرهمزمان
    logger.info("Bot is active and running via Polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
    