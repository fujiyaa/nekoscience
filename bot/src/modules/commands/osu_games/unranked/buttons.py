


from math import ceil

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .options import *



def get_keyboard(
    keyboard_type: str, 
    config: dict | None = None,    
    intake: dict | None = None,
    owner_id: int | None = None
):
    
    def with_owner(cb_data: str) -> str:
        if owner_id is not None:
            return f"{cb_data}:{owner_id}"
        return cb_data

    if keyboard_type == "main":
        if intake.get('sent_type') == 'score':
            mods_text = intake.get("sent_mods")

            if not mods_text or mods_text == "None":
                mods_text = ""
        else:
            mods = config.get("mods", [])
            mods_text = " ".join(mods) if mods else ""

        if config.get('source') == 1:
            mods = config.get("mods", [])
            mods_text = " ".join(mods) if mods else ""

        keyboard = [
            [InlineKeyboardButton(
                SOURCE_OPTIONS[config.get('source')],
                callback_data=with_owner(f"unranked_switch_source")
            )],
            [                
                InlineKeyboardButton(
                    TIME_OPTIONS[config.get('time')],
                    callback_data=with_owner(f"unranked_switch_time")
                ),
                InlineKeyboardButton(
                    GOAL_OPTIONS[config.get('goal')],
                    callback_data=with_owner(f"unranked_switch_goal")
                )
            ],
            [InlineKeyboardButton(
                f"mods... {mods_text}",
                callback_data=with_owner(f"unranked_switch_mods")
            )],
            [InlineKeyboardButton(
                CROSSCLIENT_OPTIONS[config.get('crossclient')],
                callback_data=with_owner(f"unranked_switch_crossclient")
            )],            
            [
                InlineKeyboardButton(
                    "Помощь",
                    callback_data=with_owner(f"unranked_help_display")
                ),
                InlineKeyboardButton(
                    "Удалить",
                    callback_data=with_owner(f"unranked_round_donotcreate")
                ),
                InlineKeyboardButton(
                    "✳️ Создать", 
                    callback_data=with_owner(f"unranked_round_create")
                )
            ]
        ]
    elif keyboard_type == "help":
        keyboard = [
            [InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=with_owner(f"unranked_help_back")
            )]
        ]
    elif keyboard_type == "mods":
        selected_mods = config.get("mods", [])

        keyboard = []

        row = []

        for mod in MOD_OPTIONS:
            enabled = mod in selected_mods

            text = f"✅ {mod}" if enabled else f"⬛ {mod}"

            row.append(
                InlineKeyboardButton(
                    text,
                    callback_data=with_owner(f"unranked_modtoggle_{mod}")
                )
            )

            if len(row) == 3:
                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        keyboard.append([
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=with_owner("unranked_modtoggle_back")
            )
        ])
    elif keyboard_type == "main-active":
        keyboard = [
            [InlineKeyboardButton(
                "🎯 Текущая игра", 
                callback_data=with_owner(f"unranked_???_"))
            ]
        ]    
    elif keyboard_type == "round-askformember":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🚫 Отклонить",
                    callback_data=with_owner(f"unranked_round_declinemember")
                ),
                InlineKeyboardButton(
                    "✅ Начать игру", 
                    callback_data=with_owner(f"unranked_round_join")
                )
            ]
        ]
    elif keyboard_type == "main-menu":
        # 👤 моя статистика
        # ⏳ игры с моим участием
        # 📺 все активные игры
        # 🏆 топ рейтинга
        # помощь

        keyboard = [            
            [
                InlineKeyboardButton(
                    "✳️ Создать",
                    callback_data=with_owner(f"unranked_menu_create")
                )
            ],
            [
                InlineKeyboardButton(
                    "⏳ Мои игры",
                    callback_data=with_owner(f"unranked_menu_myactive")
                ),
                # InlineKeyboardButton(
                #     "📺 Все игры",
                #     callback_data=with_owner(f"unranked_menu_allactive")
                # )
            ],
            [
                # InlineKeyboardButton(
                #     "👤 Статистика",
                #     callback_data=with_owner(f"unranked_menu_mystats")
                # ),
                InlineKeyboardButton(
                    "🏆 Топ рейтинга",
                    callback_data=with_owner(f"unranked_menu_alltop")
                )
            ],
            [InlineKeyboardButton(
                " Как играть",
                callback_data=with_owner(f"unranked_menu_helpnested")
            )]
        ]
    elif keyboard_type == "main-helpnested":
        keyboard = [
            [InlineKeyboardButton(
                "Что такое unranked плей?",
                callback_data=with_owner(f"unranked_menu_aboutgame")
            )],
            [InlineKeyboardButton(
                "Как работает рейтинг?",
                callback_data=with_owner(f"unranked_menu_aboutelo")
            )],
            [InlineKeyboardButton(
                "❗️ Как создавать и отменять раунд?",
                callback_data=with_owner(f"unranked_menu_aboutcreation")
            )],
            [InlineKeyboardButton(
                "Два режима игры?",
                callback_data=with_owner(f"unranked_menu_aboutend")
            )],
            [InlineKeyboardButton(
                "Как работает таймер?",
                callback_data=with_owner(f"unranked_menu_abouttime")
            )],           
            [InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=with_owner(f"unranked_menu_main")
            )]            
        ]
    elif keyboard_type == "main-help":
        keyboard = [
            [InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=with_owner(f"unranked_menu_helpnested")
            )]            
        ]
    elif keyboard_type == "main-back":
        keyboard = [
            [InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=with_owner(f"unranked_menu_main")
            )]            
        ]    
    else: print(f"unknown keyboard type: {keyboard_type}")
   

    return InlineKeyboardMarkup(keyboard)

def get_match_edit_keyboard(
    keyboard_type: str,
    match_id: str,
    owner_id: int
):
    def with_owner(cb_data: str) -> str:
        if owner_id is not None:
            return f"{cb_data}:{owner_id}"
        return cb_data
    
    if keyboard_type == "with-member":

        keyboard = [
            [                
                InlineKeyboardButton(
                    "❌ Сдаться",
                    callback_data=with_owner(f"unranked_matchleave_{match_id}")
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Назад",
                    callback_data=with_owner(f"unranked_menu_myactive")
                )
            ],
        ]
    elif keyboard_type == "without-member":
        keyboard = [
            [
                InlineKeyboardButton(
                    "❎ Отменить",
                    callback_data=with_owner(f"unranked_matchcancel_{match_id}")
                )                
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Назад",
                    callback_data=with_owner(f"unranked_menu_myactive")
                )
            ],
        ]
    else:
        keyboard = [           
            [
                InlineKeyboardButton(
                    "⬅️ Назад",
                    callback_data=with_owner(f"unranked_menu_myactive")
                )
            ],
        ]

    return InlineKeyboardMarkup(keyboard)

def get_active_matches_keyboard(
    active_matches: list[str],
    matches: dict,
    owner_id: int
):
    keyboard = []

    buttons = []

    for match_id in active_matches:

        match = matches.get(match_id)

        if not match:
            continue

        member = match.get("member") or {}

        short_id = match_id[-5:]

        if member:
            text = f"{short_id} ⏳"
        else:
            text = f"{short_id} ❎"

        buttons.append(
            InlineKeyboardButton(
                text=text,
                callback_data=f"unranked_matchedit_{match_id}:{owner_id}"
            )
        )

    per_row = 4

    keyboard = [
        buttons[i:i + per_row]
        for i in range(0, len(buttons), per_row)
    ]

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"unranked_menu_main:{owner_id}"
        )
    ])

    return InlineKeyboardMarkup(keyboard)

def get_round_configured_keyboard(
    match_id: int,
    owner_id: int
):
    keyboard = [
            [   
                InlineKeyboardButton(
                    "Скрыть кнопки", 
                    callback_data=f"unranked_round_hide:{owner_id}"
                ),
                InlineKeyboardButton(
                    "✅ Участвовать", 
                    callback_data=f"unranked_round_join:{match_id}"
                )
            ]
        ]
    return InlineKeyboardMarkup(keyboard)

def get_pending_join_keyboard(
    match_id: str,
    join_tg_id: str,
    owner_id: str,
):
    keyboard = [
            [   
                InlineKeyboardButton(
                    "✖️ Отклонить", 
                    callback_data=f"unranked_deny_{join_tg_id}_{match_id}:{owner_id}"
                ),
                InlineKeyboardButton(
                    "✅ Начать игру", 
                    callback_data=f"unranked_accept_{join_tg_id}_{match_id}:{owner_id}"
                )
            ]
        ]
    return InlineKeyboardMarkup(keyboard)