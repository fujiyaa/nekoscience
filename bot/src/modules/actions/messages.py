


import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import logging

from config import remove_tasks

async def delete_message_after_delay(context, chat_id: int, message_id: int, delay: int = 10):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

async def delete_response(resp, delay: int = 10):
    await asyncio.sleep(delay)
    if isinstance(resp, list):
        for r in resp:
            try:
                await r.delete()
            except Exception as e:
                print(f"Ошибка при удалении сообщения: {e}")
    else:
        try:
            await resp.delete()
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

async def safe_send_message(
        update: Update, 
        text: str, 
        parse_mode=None, 
        reply_markup=None,
        disable_web_page_preview=False
    ):
    for _ in range(5):
        try:
            if update.message:
                return await update.message.reply_text(
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview
                )

            elif update.callback_query:
                return await update.callback_query.message.reply_text(
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview
                )

            else:
                return await update.effective_chat.send_message(
                    text=text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview
                )

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

        # ошибка здесь это нормально
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

async def safe_edit_query(query, text, parse_mode=None, reply_markup=None,
                          disable_web_page_preview=True, link_preview_options=None):
    try:
        msg = query.message

        kwargs = {
            "parse_mode": parse_mode,
            "reply_markup": reply_markup
        }

        if link_preview_options is not None:
            kwargs["link_preview_options"] = link_preview_options
        else:
            kwargs["disable_web_page_preview"] = disable_web_page_preview

        if msg.text or msg.caption:
            return await msg.edit_text(text, **kwargs)

        return await msg.edit_caption(text, **kwargs)

    except Exception as e:
        print(f"safe_edit_query failed: {e}")

