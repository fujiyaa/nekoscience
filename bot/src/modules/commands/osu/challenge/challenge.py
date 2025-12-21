


from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update



# просто заглушка
async def challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)
    
    try:
        topic_id = getattr(update.effective_message, "message_thread_id", None) 
        text = "нет челленджа сегодня 😞"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, message_thread_id=topic_id, parse_mode="HTML")
        
    except Exception as e:
        print(e)