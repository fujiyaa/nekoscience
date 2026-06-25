


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo



def get_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                text="⭐️ MiniApp",
                url="https://t.me/Weakobot?startapp"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔑 Код",
                callback_data="GET_GAME_CODE"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)