


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def get_keyboard(keyboard_type: str, scores_quantity: int = 2, owner_id: int | None = None):
    
    def with_owner(cb_data: str) -> str:
        if owner_id is not None:
            return f"{cb_data}:{owner_id}"
        return cb_data

    if keyboard_type == "main":
        keyboard = [
            [InlineKeyboardButton(
                "➡️ Играть", 
                callback_data=with_owner(f"osugamehl_next_{scores_quantity}")),
            ]           
        ]
    elif keyboard_type == "main-active":
        keyboard = [
            [InlineKeyboardButton(
                "🎯 Текущая игра", 
                callback_data=with_owner(f"osugamehl_next_{scores_quantity}"))
            ]
        ]
    elif keyboard_type.startswith("next_"):
        count = int(keyboard_type.split("_")[1])
        EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        keyboard = [[
            InlineKeyboardButton(
                emoji,
                callback_data=with_owner(f"osugamehl_finish_{i}")
            )
            for i, emoji in enumerate(EMOJIS[:count], start=1)
        ]]
    elif keyboard_type == "finish":
        keyboard = [
            [InlineKeyboardButton(
                "➡️ Новая игра", 
                callback_data=with_owner(f"osugamehl_next_{scores_quantity}"))
            ]
        ]
    elif keyboard_type.startswith("finish_"):
        count = int(keyboard_type.split("_")[1])
        keyboard = [
            [InlineKeyboardButton(
                "➡️ Дальше", 
                callback_data=with_owner(f"osugamehl_next_{count}"))
            ]
        ]
        
    elif keyboard_type == "leaderboard":
        keyboard = [
            [
                InlineKeyboardButton(
                    "📑 Главное меню игры", 
                    callback_data="osugamehl_main")
            ],
        ]

    return InlineKeyboardMarkup(keyboard)
