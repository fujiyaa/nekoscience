


import temp

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.auth import check_osu_verified
from ....systems.logging import log_all_update

from config import POINTS_FILE



async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)
    
    try:
        topic_id = getattr(update.effective_message, "message_thread_id", None)        
        points_data = temp.load_json(POINTS_FILE, {})
        if not points_data:
            await context.bot.send_message(chat_id=update.effective_chat.id, message_thread_id=topic_id, text="🏆 Лидерборд пуст", parse_mode="HTML")
            return
        
        sorted_lb = sorted(points_data.items(), key=lambda x: x[1], reverse=True)
        text = "🏆 <b>Лидерборд челленджей:</b>\n"
        for i, (uid, pts) in enumerate(sorted_lb[:10], start=1):
            saved_name = await check_osu_verified(str(uid))
            display_name = saved_name if saved_name else uid 
            text += f"{i}. {display_name} — <b><u>{pts}</u></b>pt\n"

        text += f"\n\n👑 <b>Сезонный:</b>\n n/a"

        await context.bot.send_message(chat_id=update.effective_chat.id, message_thread_id=topic_id, text=text, parse_mode="HTML")
    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, message_thread_id=topic_id, text=f"ошибка {e}", parse_mode="HTML")
