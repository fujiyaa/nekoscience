


from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo



def get_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                text="⭐️ MiniApp",
                web_app=WebAppInfo(
                    url="https://myangelfujiya.ru/game"
                )
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)