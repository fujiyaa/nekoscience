


import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import logging

from bot.src.config import remove_tasks

async def delete_message_after_delay(context, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

async def delete_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE, delay: int = 5):
    if not update.message:
        return

    chat_id = update.message.chat_id
    message_id = update.message.message_id

    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка при удалении пользовательского сообщения: {e}")

async def safe_send_message(update: Update, text: str, parse_mode=None):
    for _ in range(5):
        try:
            return await update.message.reply_text(text, parse_mode=parse_mode)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения: {e}")
            await asyncio.sleep(1)
    logging.error("Не удалось отправить сообщение после 5 попыток.")
    return None

async def try_send(coro_func, *args, retries=3, delay=1, **kwargs):
    for attempt in range(retries):
        try:
            return await coro_func(*args, **kwargs)
        except Exception as e:
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                print(f"Failed after {retries} attempts: {e}")
                return None


def reset_remove_timer(bot, chat_id, msg_id, delay=30, cleanup=None):    
    if msg_id in remove_tasks:
        remove_tasks[msg_id].cancel()

    async def delayed():
        await asyncio.sleep(delay)
        try:
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=None
            )
        except Exception:
            pass
        finally:
            remove_tasks.pop(msg_id, None)
            if cleanup:
                cleanup()

    task = asyncio.create_task(delayed())
    remove_tasks[msg_id] = task




#retries

async def safe_query_answer(query, text=None, show_alert=True, retries=2, delay=1):
    attempt = 0
    while attempt <= retries:
        try:
            if text is not None:
                await query.answer(text, show_alert=show_alert)
            else:
                await query.answer()
            return
        except Exception as e:
            attempt += 1
            if attempt > retries:
                print(f"❌ Не удалось отправить ответ: {e}")
                return
            await asyncio.sleep(delay)

async def safe_edit_message(message, text, parse_mode=None, reply_markup=None):
    try:       
        if message and (message.text or message.caption):
            return await message.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
        else:
            return await message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    except Exception as e:
        print(f"safe_edit_message failed: {e}")
        return await message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup) 
