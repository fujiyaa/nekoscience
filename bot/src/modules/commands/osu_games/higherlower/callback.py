


import traceback
from telegram import Update
from telegram.ext import ContextTypes

from ....actions.messages import safe_query_answer
from .actions.finish import finish_game
from .actions.next import next_game
from .higherlower import higherlower_game

from config import SUPPORT_STUB, MAX_TEXT_LENGTH



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    try:
        payload = data.removeprefix("osugamehl_")  # "finish_2:1803166423"

        if ":" in payload:
            main_part, owner_id_str = payload.rsplit(":", 1)
            owner_id = int(owner_id_str)
        else:
            main_part = payload
            owner_id = None

        parts = main_part.split("_")  # ["finish", "2"]
        action = parts[0]
        arg = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

        if owner_id is not None and query.from_user.id != owner_id:
            await query.answer("❔ Чужие кнопки", show_alert=True)
            return

        actions = {
            "next": next_game,
            "finish": finish_game,
            "main": higherlower_game
        }

        if action in actions:
            if arg is not None:
                await actions[action](update, context, arg)
            else:
                await actions[action](update, context)
        else:
            await query.edit_message_text("Неизвестная кнопка!")

        await safe_query_answer(query, show_alert=False)

    except Exception:
        error_details = traceback.format_exc()
        full_text = f"{error_details}\n\n{SUPPORT_STUB}"

        sended = await safe_query_answer(query, text=full_text, show_alert=True)
        if sended:
            return

        try:
            for i in range(0, len(full_text), MAX_TEXT_LENGTH):
                chunk = full_text[i:i + MAX_TEXT_LENGTH]
                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text=chunk
                )
        except Exception as e:
            print(e)