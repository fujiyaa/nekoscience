


from telegram import InlineKeyboardButton

from ....wrappers.settings import get_settings_text

from ....systems.translations import TRANSLATIONS as T
from .defaults import SETTINGS, CATEGORIES



def _mark(value: bool) -> str:
    return "☑️" if value else "❌"


def main_menu(settings_service, user_id, user_name: str):
    lang = settings_service.get(user_id, "lang")

    keyboard = []

    sorted_categories = sorted(
        CATEGORIES.items(),
        key=lambda x: x[1]["order"]
    )

    for category, meta in sorted_categories:
        keyboard.append([
            InlineKeyboardButton(
                T[meta["title"]][lang],
                callback_data=f"settings_category:{category}:{user_id}"
            )
        ])

    text = T["settings_title"][lang]

    text = get_settings_text(text, user_name, True)

    return keyboard, text

def category_menu(settings_service, user_id, category: str, user_name: str):
    lang = settings_service.get(user_id, "lang")

    keyboard = []

    for key, info in SETTINGS.items():

        if info["category"] != category:
            continue

        ui = info.get("ui", "toggle")
        value = settings_service.get(user_id, key)

        if ui == "toggle":
            keyboard.append([
                InlineKeyboardButton(
                    f"{T[key][lang]}  {_mark(value)}",
                    callback_data=f"settings_toggle:{key}:{user_id}"
                )
            ])

        elif ui == "select" and key == "lang":
            keyboard.append([
                InlineKeyboardButton(
                    f"🇷🇺 Русский{'🔘' if value == 'ru' else ''}",
                    callback_data=f"settings_set:lang:ru:{user_id}"
                ),
                InlineKeyboardButton(
                    f"🇬🇧 English{'🔘' if value == 'en' else ''}",
                    callback_data=f"settings_set:lang:en:{user_id}"
                ),
            ])

    keyboard.append([
        InlineKeyboardButton(
            T["settings_back"][lang],
            callback_data=f"settings_main:{user_id}"
        )
    ])

    text = f'{T["settings_title"][lang]} {T[CATEGORIES[category]["title"]][lang]}'
    
    text = get_settings_text(text, user_name)

    return keyboard, text