


from telegram import InlineKeyboardButton

from ....systems.translations import TRANSLATIONS as TR



async def get_settings_kb(user_id, user_data): 
    user_settings = user_data.get(str(user_id), {}) 
    lang_code = user_settings.get("lang", "ru")   
    bg_code = user_settings.get("rs_bg_render", False) 
    display_fails = user_settings.get("display_fails", True) 
    display_more_scores = user_settings.get("display_more_scores", False) 
    
    if lang_code == "en":
        en_flag = "✅"
        ru_flag = ""
    else:
        en_flag = ""
        ru_flag = "✅"
    
    if bg_code:
        bg_y_flag = "✅"
        bg_n_flag = ""
    else:
        bg_y_flag = ""
        bg_n_flag = "❌"

    if display_fails:
        display_fails_y = "✅"
        display_fails_n = ""
    else:
        display_fails_y = ""
        display_fails_n = "❌"

    if display_more_scores:
        display_more_scores_y = "✅"
        display_more_scores_n = ""
    else:
        display_more_scores_y = ""
        display_more_scores_n = "❌"

    keyboard = [
        # [
        #     InlineKeyboardButton(
        #         f"🎨 {TR['settings_rs_title'][lang_code]}",
        #         callback_data=f"settings_ignore:{user_id}"
        #     )
        # ],
        # [
        #     InlineKeyboardButton(
        #         f"{TR['settings_yes'][lang_code]} {bg_y_flag}",
        #         callback_data=f"settings_rs_bg_yes:{user_id}"
        #     ),           
        #     InlineKeyboardButton(
        #         f"{TR['settings_no'][lang_code]} {bg_n_flag}",
        #         callback_data=f"settings_rs_bg_no:{user_id}"
        #     )
        # ],
        [
            InlineKeyboardButton(
                f"{TR['settings_rs_fails'][lang_code]}",
                callback_data=f"settings_ignore:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{TR['fails_yes'][lang_code]} {display_fails_y}",
                callback_data=f"settings_display_fails_y:{user_id}"
            ),           
            InlineKeyboardButton(
                f"{TR['fails_no'][lang_code]} {display_fails_n}",
                callback_data=f"settings_display_fails_n:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{TR['settings_sc_more_scores'][lang_code]}",
                callback_data=f"settings_ignore:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{TR['fails_yes'][lang_code]} {display_more_scores_y}",
                callback_data=f"settings_display_scores_y:{user_id}"
            ),           
            InlineKeyboardButton(
                f"{TR['fails_no'][lang_code]} {display_more_scores_n}",
                callback_data=f"settings_display_scores_n:{user_id}"
            )
        ],
        # [
        #     InlineKeyboardButton(
        #         f"🖼 {TR['settings_card_title'][lang_code]}",
        #         callback_data=f"settings_ignore:{user_id}"
        #     )
        # ],
        # [
        #     InlineKeyboardButton(
        #         f"{TR['settings_new'][lang_code]} {new_card_flag}",
        #         callback_data=f"settings_new_card:{user_id}"
        #     ),           
        #     InlineKeyboardButton(
        #         f"{TR['settings_old'][lang_code]} {old_card_flag}",
        #         callback_data=f"settings_old_card:{user_id}"
        #     )
        # ],
        [
            InlineKeyboardButton(
                f"🌐 {TR['lang'][lang_code]}",
                callback_data=f"settings_ignore:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{TR['english'][lang_code]} {en_flag}",
                callback_data=f"settings_english:{user_id}"
            ),           
            InlineKeyboardButton(
                f"{TR['russian'][lang_code]} {ru_flag}",
                callback_data=f"settings_russian:{user_id}"
            )
        ]
    ]

    text = TR['settings_title'][lang_code]

    return keyboard, text
