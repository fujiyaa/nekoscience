


from telegram import InlineKeyboardButton

from ....systems.translations import TRANSLATIONS as T



async def get_settings_kb(user_id, user_data): 
    user_settings = user_data.get(str(user_id), {}) 
    l = user_settings.get("lang", "ru")   
    # bg_code = user_settings.get("rs_bg_render", False) 
    display_fails = user_settings.get("display_fails", True)
    display_fails_average_recent = user_settings.get("display_fails_average_recent", True) 
    display_more_scores = user_settings.get("display_more_scores", False) 
    settings_score_card = user_settings.get("settings_score_card", False)
    
    if l == "en":
        en_flag = "✅"
        ru_flag = ""
    else:
        en_flag = ""
        ru_flag = "✅"
    
    def mark(value: bool) -> str:
        return "✅" if value else "❌"

    
    display_fails_x = mark(display_fails)
    display_fails_ar_x = mark(display_fails_average_recent)
    display_more_scores_x = mark(display_more_scores)
    settings_score_card_x = mark(settings_score_card)
    # bg_code_x = mark(bg_code)

    rs_fails = 'settings_rs_fails'
    avg_fails = 'settings_ar_fails'
    more_scores = 'settings_sc_more_scores' 
    score_card = 'settings_score_card'

    keyboard = [
        [
            InlineKeyboardButton(
                f"{T[rs_fails][l]} {display_fails_x}",
                callback_data=f"{rs_fails}:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{T[avg_fails][l]} {display_fails_ar_x}",
                callback_data=f"{avg_fails}:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{T[more_scores][l]} {display_more_scores_x}",
                callback_data=f"{more_scores}:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{T[score_card][l]} {settings_score_card_x}",
                callback_data=f"score_card:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{T['english'][l]} {en_flag}",
                callback_data=f"settings_english:{user_id}"
            ),           
            InlineKeyboardButton(
                f"{T['russian'][l]} {ru_flag}",
                callback_data=f"settings_russian:{user_id}"
            )
        ]
    ]

    text = T['settings_title'][l]

    return keyboard, text
