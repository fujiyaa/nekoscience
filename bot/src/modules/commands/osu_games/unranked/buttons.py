


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
            [InlineKeyboardButton(
                POLICY_OPTIONS[config.get('policy')],
                callback_data=with_owner(f"unranked_switch_policy")
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
    elif keyboard_type == "round-configured":
        keyboard = [
            [   
                InlineKeyboardButton(
                    "Отменить", 
                    callback_data=with_owner(f"unranked_round_donotcreate")
                ),
                InlineKeyboardButton(
                    "✅ Участвовать", 
                    callback_data=with_owner(f"unranked_round_join")
                )
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
   

    return InlineKeyboardMarkup(keyboard)
