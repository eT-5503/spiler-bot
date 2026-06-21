from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_warning_template(title: str, views: int = 0) -> str:
    """قالب استاندارد و درخواستی پیام هشدار اسپویلر"""
    return (
        "⚠️ **هشدار اسپویل**\n\n"
        f"🎬 **{title}**\n\n"
        "این پیام حاوی اطلاعات مهمی از داستان است.\n\n"
        "قبل از مشاهده مطمئن شوید\n"
        "این اثر را دیده‌اید.\n\n"
        "🔓 برای مشاهده روی دکمه زیر کلیک کنید\n\n"
        f"👁️ {views} بازدید"
    )

def get_spoiler_keyboard(spoiler_id: int) -> InlineKeyboardMarkup:
    """ساخت دکمه شیشه‌ای متصل به شناسه دیتابیس اسپویلر"""
    keyboard = [[InlineKeyboardButton("🔓 نمایش اسپویل", callback_data=f"show_{spoiler_id}")]]
    return InlineKeyboardMarkup(keyboard)
    