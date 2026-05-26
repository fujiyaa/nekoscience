


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def get_keyboard():

    keyboard = [
        [
            InlineKeyboardButton(
                text="⭐️ Авторизовать никнейм",
                url="https://myangelfujiya.ru/weakness/auth"
            )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)