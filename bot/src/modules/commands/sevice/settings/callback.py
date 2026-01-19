


import temp

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ....actions.messages import safe_query_answer
from .buttons import get_settings_kb

from config import USER_SETTINGS_FILE



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    name = str(query.from_user.name)
    action, owner_id = query.data.split(":")

    if user_id != owner_id:
        await safe_query_answer(query, "Чужая кнопка") 
        return

    settings = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = settings.get(str(user_id), {
            "lang": "ru", 
            "notify": True, 
            "rs_bg_render": False, 
            "new_card": True,
            "display_fails": True,
            "display_more_scores": False,
        })    

    if action == "settings_english":
        user_settings["lang"] = "en"
        await safe_query_answer(query) 

    elif action == "settings_russian":
        user_settings["lang"] = "ru"
        await safe_query_answer(query) 

    elif action == "settings_rs_bg_yes":
        user_settings["rs_bg_render"] = True
        await safe_query_answer(query) 

    elif action == "settings_rs_bg_no":
        user_settings["rs_bg_render"] = False
        await safe_query_answer(query) 

    elif action == "settings_display_fails_y":
        user_settings["display_fails"] = True
        await safe_query_answer(query) 

    elif action == "settings_display_fails_n":
        user_settings["display_fails"] = False
        await safe_query_answer(query) 

    elif action == "settings_display_scores_y":
        user_settings["display_more_scores"] = True
        await safe_query_answer(query) 

    elif action == "settings_display_scores_n":
        user_settings["display_more_scores"] = False
        await safe_query_answer(query) 

    elif action == "settings_new_card":
        user_settings["new_card"] = True
        await safe_query_answer(query) 

    elif action == "settings_old_card":
        user_settings["new_card"] = False
        await safe_query_answer(query) 

    elif action == "settings_ignore":
        await safe_query_answer(query) 

    settings[user_id] = user_settings
    temp.save_json(USER_SETTINGS_FILE, settings)

    kb, text = await get_settings_kb(user_id, settings)

    try:
        await query.edit_message_text(
            f'{text} {name}',
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except Exception as e:
        await query.answer()
