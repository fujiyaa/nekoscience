from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ....actions.messages import safe_query_answer
from ....actions.rich import edit_rich_query

from .defaults import SETTINGS
from .menu import main_menu, category_menu
from .service import neko_settings

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    name = query.from_user.name


    parts = query.data.split(":")
    action = parts[0]

    if len(parts) < 2:
        return

    try:
        owner_id = int(parts[-1])

        if owner_id != user_id:
            await query.answer("Чужие кнопки", show_alert=False)
            return
    except:
        await query.answer("Ошибка кнопки...", show_alert=False)
        return

    
    await safe_query_answer(query)

    #
    # settings
    #

    if action == "settings_main":

        kb, text = main_menu(
            neko_settings, 
            user_id,
            name
        )

    #
    # settings_category:<category>
    #

    elif action == "settings_category":

        category = parts[1]

        kb, text = category_menu(
            neko_settings,
            user_id,
            category,
            name
        )

    #
    # settings_toggle:<setting>
    #

    elif action == "settings_toggle":

        key = parts[1]

        neko_settings.toggle(user_id, key)

        category = SETTINGS[key]["category"]

        kb, text = category_menu(
            neko_settings,
            user_id,
            category,
            name
        )

    #
    # settings_set:<setting>:<value>
    #

    elif action == "settings_set":

        key = parts[1]
        value = parts[2]

        ui = SETTINGS[key].get("ui", "toggle")

        if ui == "toggle":
            neko_settings.toggle(user_id, key)

        elif ui == "select":
            neko_settings.set(user_id, key, value)

        category = SETTINGS[key]["category"]

        kb, text = category_menu(
            neko_settings,
            user_id,
            category,
            name
        )

    else:
        return

    try:
        await edit_rich_query(
            query=query,
            markdown=text,
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except Exception:
        pass