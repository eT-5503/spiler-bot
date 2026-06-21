from telegram import Update
from telegram.ext import ContextTypes
from database import db

async def handle_top_spoilers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست رتبه‌بندی کاربران برتر بر اساس تعداد ارسال اسپویلر"""
    chat = update.effective_chat
    
    if chat.type not in ["group", "supergroup"]:
        await update.effective_message.reply_text("❌ این دستور فقط در گروه‌ها قابل استفاده است.")
        return

    top_users = await db.get_top_spoilers(limit=10)
    
    if not top_users:
        await update.effective_message.reply_text("🏆 هنوز هیچ اسپویلی در این گروه ثبت نشده است!")
        return
        
    response = "🏆 **اسپویلرهای برتر گروه**\n\n"
    for idx, row in enumerate(top_users, start=1):
        username = row["username"]
        count = row["spoiler_count"]
        # خنثی‌سازی کاراکترهای مارک‌داون در یوزرنیم‌ها برای جلوگیری از اختلال در متن
        clean_username = username.replace("_", "\\_").replace("*", "\\*")
        response += f"{idx}. {clean_username} — {count} اسپویل\n"
        
    await update.effective_message.reply_text(response, parse_mode="Markdown")
    