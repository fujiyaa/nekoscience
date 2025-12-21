


from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from bot.src.modules.systems.translations import TRANSLATIONS as TR



async def get_settings_kb(user_id, user_data):
    

    user_settings = user_data.get(str(user_id), {}) 
    lang_code = user_settings.get("lang", "ru")   
    bg_code = user_settings.get("rs_bg_render", False) 
    new_card = user_settings.get("new_card", True) 

    
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
        bg_n_flag = "✅"

    if new_card:
        new_card_flag = "✅"
        old_card_flag = ""
    else:
        new_card_flag = ""
        old_card_flag = "✅"

    keyboard = [
        [
            InlineKeyboardButton(
                f"🎨 {TR['settings_rs_title'][lang_code]}",
                callback_data=f"settings_ignore:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{TR['settings_yes'][lang_code]} {bg_y_flag}",
                callback_data=f"settings_rs_bg_yes:{user_id}"
            ),           
            InlineKeyboardButton(
                f"{TR['settings_no'][lang_code]} {bg_n_flag}",
                callback_data=f"settings_rs_bg_no:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"🖼 {TR['settings_card_title'][lang_code]}",
                callback_data=f"settings_ignore:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                f"{TR['settings_new'][lang_code]} {new_card_flag}",
                callback_data=f"settings_new_card:{user_id}"
            ),           
            InlineKeyboardButton(
                f"{TR['settings_old'][lang_code]} {old_card_flag}",
                callback_data=f"settings_old_card:{user_id}"
            )
        ],
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

def get_pagination_keyboard_choke(page, total_pages, user_id):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}_{user_id}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("След. страница ➡️", callback_data=f"page_{page+1}_{user_id}"))
    return InlineKeyboardMarkup([buttons]) if buttons else None

def create_pagination_keyboard(page, total_pages, user_id):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"farm_page:{user_id}:{page-1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("➡️ Вперёд", callback_data=f"farm_page:{user_id}:{page+1}"))
    return InlineKeyboardMarkup([buttons])

def get_farm_step_keyboard(step):
    if step == 1:
        buttons = [
            [
                InlineKeyboardButton("30%", callback_data="farm_skill:1"),
                InlineKeyboardButton("40%", callback_data="farm_skill:2"),
                InlineKeyboardButton("50%", callback_data="farm_skill:3"),
                InlineKeyboardButton("60%", callback_data="farm_skill:4"),
                InlineKeyboardButton("70%", callback_data="farm_skill:5"),
            ],
            [
                InlineKeyboardButton("80%", callback_data="farm_skill:6"),
                InlineKeyboardButton("90%", callback_data="farm_skill:7"),
                InlineKeyboardButton("100%", callback_data="farm_skill:8"),
                InlineKeyboardButton("110%", callback_data="farm_skill:9"),
                InlineKeyboardButton("120%", callback_data="farm_skill:10"),
            ]            
        ]
    elif step == 3:
        buttons = [
            [
                InlineKeyboardButton("NM", callback_data="farm_mod:NM"),
                InlineKeyboardButton("HD", callback_data="farm_mod:HD"),
                InlineKeyboardButton("HR", callback_data="farm_mod:HR"),                
                InlineKeyboardButton("DT", callback_data="farm_mod:DT"),
                
            ],
            [   
                InlineKeyboardButton("HDHR", callback_data="farm_mod:HDHR"),                
                InlineKeyboardButton("HDDT", callback_data="farm_mod:DTHD"),
                InlineKeyboardButton("DTHR", callback_data="farm_mod:DTHR"),
                InlineKeyboardButton("HDDTHR", callback_data="farm_mod:DTHDHR")
            ]
        ]
    elif step == 0:
        buttons = [
            [
                InlineKeyboardButton("Клиент Stable", callback_data="farm_lazer:False"),            
                InlineKeyboardButton("Клиент Lazer", callback_data="farm_lazer:True"),
            ],
            
        ]
    elif step == 2:
        buttons = [
            [
                InlineKeyboardButton("±10%", callback_data="farm_tol:1.1"),
                InlineKeyboardButton("±20%", callback_data="farm_tol:1.2"),
                InlineKeyboardButton("±30%", callback_data="farm_tol:1.3"),
                InlineKeyboardButton("±40%", callback_data="farm_tol:1.4"),
                InlineKeyboardButton("±50%", callback_data="farm_tol:1.5"),
            ],
            [
                InlineKeyboardButton("±60%", callback_data="farm_tol:1.6"),
                InlineKeyboardButton("±70%", callback_data="farm_tol:1.7"),
                InlineKeyboardButton("±80%", callback_data="farm_tol:1.8"),
                InlineKeyboardButton("±90%", callback_data="farm_tol:1.9"),
                InlineKeyboardButton("±100%", callback_data="farm_tol:2.0"),
            ]
        ]
    else:
        buttons = []
    return InlineKeyboardMarkup(buttons)
