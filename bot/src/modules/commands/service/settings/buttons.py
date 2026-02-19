from telegram import InlineKeyboardButton
from ....systems.translations import TRANSLATIONS as T

FIGURE_SPACE = "\u2007"  # фиксированная ширина

async def get_settings_kb(user_id, user_data):
    user_settings = user_data.get(str(user_id), {})
    l = user_settings.get("lang", "ru")

    # Булевы настройки: (ключ в user_settings, ключ в TRANSLATIONS)
    bool_settings = [
        ("display_fails", "settings_rs_fails"),
        ("display_fails_average_recent", "settings_ar_fails"),
        ("display_more_scores", "settings_sc_more_scores"),
        ("settings_score_card", "settings_score_card"),
    ]

    def mark(value: bool) -> str:
        return "☑️" if value else "❌"

    # Находим максимальную длину текста
    max_len = max(len(T[tr_key][l]) for _, tr_key in bool_settings)

    keyboard = []

    for field, tr_key in bool_settings:
        val = user_settings.get(field, False)
        text = T[tr_key][l]
        padded_text = text +  FIGURE_SPACE * 2 + FIGURE_SPACE * (max_len - len(text)) * 3 + " " + mark(val)
        keyboard.append([
            InlineKeyboardButton(
                padded_text,
                callback_data=f"{tr_key}:{user_id}"
            )
        ])

    en_flag = "🔘" if l == "en" else ""
    ru_flag = "🔘" if l == "ru" else ""
    keyboard.append([
        InlineKeyboardButton(
            f"{T['english'][l]} {en_flag}",
            callback_data=f"settings_english:{user_id}"
        ),
        InlineKeyboardButton(
            f"{T['russian'][l]} {ru_flag}",
            callback_data=f"settings_russian:{user_id}"
        )
    ])

    text = T['settings_title'][l]
    return keyboard, text
