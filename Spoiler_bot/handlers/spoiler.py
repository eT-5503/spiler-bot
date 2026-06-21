import logging
import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from config import DB_PATH
from database import db
from utils.helpers import get_warning_template, get_spoiler_keyboard

logger = logging.getLogger(__name__)

async def handle_sp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دریافت و ثبت دستور /sp"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type not in ["group", "supergroup"]:
        await message.reply_text("❌ این دستور فقط در گروه‌ها قابل استفاده است.")
        return

    # بررسی و استخراج محتوای پس از دستور
    text_content = message.text[4:].strip() if message.text.startswith("/sp ") else message.text[3:].strip()
    
    if not text_content or "|" not in text_content:
        await message.reply_text("❌ فرمت دستور اشتباه است.\n\nمثال:\n`/sp Naruto | اوبیتو همان توبی است`")
        return
    
    title, spoiler_text = map(str.strip, text_content.split("|", 1))
    
    if not title or not spoiler_text:
        await message.reply_text("❌ نام اثر یا متن اسپویل نمی‌تواند خالی باشد.")
        return

    # حذف پیام لو رفته اصلی در گروه
    try:
        await message.delete()
    except TelegramError as e:
        logger.warning(f"Could not delete message in chat {chat.id}: {e}")
        await message.reply_text("⚠️ ربات برای عملکرد صحیح به دسترسی 'Delete Messages' (حذف پیام‌ها) نیاز دارد.")
        return

    # ذخیره در پایگاه داده
    username = user.username if user.username else user.first_name
    spoiler_id = await db.add_spoiler(
        chat_id=chat.id,
        user_id=user.id,
        username=username,
        title=title,
        spoiler_text=spoiler_text
    )
    
    # ارسال پیام با قالب درخواستی
    initial_text = get_warning_template(title, views=0)
    reply_markup = get_spoiler_keyboard(spoiler_id)
    
    warning_msg = await context.bot.send_message(
        chat_id=chat.id,
        text=initial_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    # ثبت شناسه نهایی پیام هشدار
    await db.update_warning_message_id(spoiler_id, warning_msg.message_id)


async def handle_spoiler_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت کلیک روی دکمه نمایش اسپویلر با منطق تفکیک ۱۸۰ کاراکتری"""
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    
    # استخراج شناسه از کال‌بک دکمه
    data_parts = query.data.split("_")
    if len(data_parts) != 2 or not data_parts[1].isdigit():
        await query.answer(text="❌ دکمه نامعتبر است.", show_alert=True)
        return
        
    spoiler_id = int(data_parts[1])
    
    # جستجوی قطعی اطلاعات اسپویل مستقیم از روی ID جدول
    spoiler = None
    async with aiosqlite.connect(DB_PATH) as _db:
        _db.row_factory = aiosqlite.Row
        async with _db.execute("SELECT * FROM spoilers WHERE id = ?", (spoiler_id,)) as cursor:
            spoiler = await cursor.fetchone()

    if not spoiler:
        await query.answer(text="❌ این اسپویل در سیستم یافت نشد یا پاک شده است.", show_alert=True)
        return

    spoiler_text = spoiler["spoiler_text"]
    title = spoiler["title"]
    
    # فرآیند ثبت بازدید یکتا
    is_new_view = await db.add_view_if_unique(spoiler_id, user.id)
    current_views = await db.get_view_count(spoiler_id)
    
    if is_new_view:
        updated_text = get_warning_template(title, views=current_views)
        reply_markup = get_spoiler_keyboard(spoiler_id)
        try:
            await query.edit_message_text(text=updated_text, reply_markup=reply_markup, parse_mode="Markdown")
        except TelegramError:
            pass

    # پیاده‌سازی منطق تفکیک بر اساس طول متن
    if len(spoiler_text) <= 180:
        # متن کوتاه: باز کردن یک برگه کوچک آلرت در داخل خود گروه
        alert_message = f"🎬 {title}:\n\n{spoiler_text}"
        await query.answer(text=alert_message, show_alert=True)
    else:
        # متن بلند: نمایش آلرت راهنما و فرستادن اطلاعات کامل به پیوی کاربر
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=f"🎬 **اسپویل طولانی اثر:** {title}\n\n💬 **متن داستان:**\n{spoiler_text}",
                parse_mode="Markdown"
            )
            await query.answer(text="📖 این اسپویل طولانی است. در حال ارسال به گفتگوی خصوصی...", show_alert=True)
        except TelegramError:
            # در صورتی که کاربر تا به حال ربات را در چت خصوصی استارت نکرده باشد
            await query.answer(text="❌ خطا! برای دریافت اسپویل‌های طولانی، ابتدا باید ربات را در پیوی خود استارت (Start) کنید.", show_alert=True)
            