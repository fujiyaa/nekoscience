


import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from .....actions.messages import safe_send_message, delete_message_after_delay, delete_user_message

from config import TARGET_CHAT_ID, CHALLENGE_TOPIC_ID



async def filter_other_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id if update.effective_chat else None
        message = update.effective_message
        thread_id = getattr(message, 'message_thread_id', None)

        text = "⚠ Можно использовать только в топике для челленджей" 
        link = "https://t.me/fujiyaosu/85927"
        if chat_id == TARGET_CHAT_ID and thread_id != CHALLENGE_TOPIC_ID:
            await safe_send_message(update, f"{text}\n{link}", parse_mode="Markdown")
            asyncio.create_task(delete_message_after_delay(context, message.chat.id, message.message_id, 5))
            asyncio.create_task(delete_user_message(update, context, delay=4))
            return False

        return True
    except: return True
