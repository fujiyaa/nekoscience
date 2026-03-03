


from telegram import Update
from telegram.ext import ContextTypes

from ....actions.messages import safe_query_answer
from .actions.finish import finish_game
from .actions.next import next_game
# from .settings import settings_game
from .higherlower import higherlower_game

from config import SUPPORT_STUB



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    # await query.answer()

    try:
        payload = data.removeprefix("osugamehl_")
        parts = payload.split("_")

        action = parts[0]
        arg = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

        actions = {
            "next": next_game,
            "finish": finish_game,
            # "settings": settings_game,
            # "help": display_help,
            "main": higherlower_game,
        }

        try:
            if action in actions:
                if arg is not None:                
                    await actions[action](update, context, arg)
                else:
                    await actions[action](update, context)
            else:
                await query.edit_message_text("Неизвестная кнопка!")

            await safe_query_answer(
                query,
                show_alert=False
            )

        except Exception as e:
            await safe_query_answer(
                query,
                text=f'ошибка: {e}\n\n{SUPPORT_STUB}',
                show_alert=True
            )

    except Exception as e:
        print(e)

