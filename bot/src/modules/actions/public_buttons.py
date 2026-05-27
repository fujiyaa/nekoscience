

import asyncio

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

state_tasks = {}  # msg_id -> task



def get_keyboard(state: str = 'hidden', beatmap_id: str = '0', search_term: str = None):

    if search_term is None:
        search_term = beatmap_id

    if state == 'hidden':
        keyboard = [
            [
                InlineKeyboardButton("...", callback_data=f"pkb:map:{beatmap_id}")
            ]
        ]
    else:
        keyboard = [
            [         
                InlineKeyboardButton(
                    "🎶 Трек",
                    callback_data=f"pm_map:{beatmap_id}"
                ),      
                InlineKeyboardButton(
                    "📨 Получить",
                    callback_data=f"muz_context:pkbmap:{beatmap_id}:67"
                ),
                InlineKeyboardButton(
                    "🔍",
                    switch_inline_query_current_chat=f"map {search_term}"
                ),                
            ]
        ]

    return InlineKeyboardMarkup(keyboard)

def schedule_keyboard_reset(bot, chat_id, msg_id, beatmap_id, delay=10):
    
    # убиваем старый таймер если есть
    if msg_id in state_tasks:
        state_tasks[msg_id].cancel()

    async def delayed():
        await asyncio.sleep(delay)

        try:
            # возвращаем keyboard в hidden состояние
            await bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=get_keyboard('hidden', beatmap_id)
            )
        except Exception:
            pass
        finally:
            state_tasks.pop(msg_id, None)

    task = asyncio.create_task(delayed())
    state_tasks[msg_id] = task

async def map_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data  # pkb:map:{beatmap_id}

    try:
        _, _, beatmap_id = data.split(":")
    except ValueError:
        return

    chat_id = query.message.chat_id
    msg_id = query.message.message_id

    await context.bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=msg_id,
        reply_markup=get_keyboard('public', beatmap_id)
    )

    schedule_keyboard_reset(
        bot=context.bot,
        chat_id=chat_id,
        msg_id=msg_id,
        beatmap_id=beatmap_id,
        delay=30
    )