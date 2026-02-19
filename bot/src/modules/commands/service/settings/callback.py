


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

    # Разбираем callback_data
    parts = query.data.split(":")
    if len(parts) < 2:
        await query.answer("Неверная кнопка")
        return

    setting_key = parts[0]
    user_id_in_data = parts[-1]

    if user_id != user_id_in_data:
        await query.answer("Чужая кнопка")
        return

    # Загружаем настройки
    settings = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = settings.get(user_id, {
        "lang": "ru", 
        "notify": True, 
        "rs_bg_render": False, 
        "new_card": True,
        "display_fails": True,
        "display_fails_average_recent": True,
        "display_more_scores": False,
        "settings_score_card": False,
    })

    # Обработка булевых настроек
    bool_settings_map = {
        "settings_score_card": "settings_score_card",
        "settings_sc_more_scores": "display_more_scores",
        "settings_rs_fails": "display_fails",
        "settings_ar_fails": "display_fails_average_recent",
    }

    if setting_key in bool_settings_map:
        # инвертируем текущее значение
        field = bool_settings_map[setting_key]
        user_settings[field] = not user_settings.get(field, False)
        await safe_query_answer(query)

    elif setting_key == "settings_english":
        user_settings["lang"] = "en"
        await safe_query_answer(query)

    elif setting_key == "settings_russian":
        user_settings["lang"] = "ru"
        await safe_query_answer(query)

    # Сохраняем и обновляем клавиатуру
    settings[user_id] = user_settings
    temp.save_json(USER_SETTINGS_FILE, settings)

    kb, text = await get_settings_kb(user_id, settings)
    try:
        await query.edit_message_text(
            f'{text} {name}',
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except Exception:
        await query.answer()
