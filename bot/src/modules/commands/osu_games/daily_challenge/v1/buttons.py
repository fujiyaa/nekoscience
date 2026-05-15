


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def get_keyboard(keyboard_type: str):
    if keyboard_type == "main":
        keyboard = [
            [InlineKeyboardButton(
                    "➡️ Новый челлендж", 
                    callback_data="challenge_next"
            )],
            [InlineKeyboardButton(
                    "🫖 Без челленджа", 
                    callback_data="challenge_justamap"
            )],
            [
                InlineKeyboardButton(
                    "🏆 Топ дейли", 
                    callback_data="challenge_leaderboard"),
                InlineKeyboardButton(
                    "ℹ️ Помощь", 
                    callback_data="challenge_info"),
            ],
        ]
    elif keyboard_type == "main-active":
        keyboard = [
            [InlineKeyboardButton(
                "🎯 Текущий челлендж", 
                callback_data="challenge_next")],            
            [
                InlineKeyboardButton(
                    "🏆 Топ дейли", 
                    callback_data="challenge_leaderboard"),
                InlineKeyboardButton(
                    "ℹ️ Помощь", 
                    callback_data="challenge_info"),
            ],
        ]
    elif keyboard_type == "next":
        keyboard = [
            [InlineKeyboardButton(
                "⏭️ пропустить", 
                callback_data="challenge_skip"),
            InlineKeyboardButton(
                "☑️ завершить", 
                callback_data="challenge_finish")]
        ]
    elif keyboard_type == "skip":
        keyboard = [
            [InlineKeyboardButton(
                "➡️ Новый челлендж", 
                callback_data="challenge_next")],
            [
                InlineKeyboardButton(
                    "🏆 Топ дейли", 
                    callback_data="challenge_leaderboard"),
                InlineKeyboardButton(
                    "ℹ️ Помощь", 
                    callback_data="challenge_info"),
            ],
        ]
    elif keyboard_type == "finish":
        keyboard = [
            [InlineKeyboardButton(
                "➡️ Новый челлендж", 
                callback_data="challenge_next")],
            [
                InlineKeyboardButton(
                    "🏆 Топ дейли", 
                    callback_data="challenge_leaderboard"),
                InlineKeyboardButton(
                    "ℹ️ Помощь", 
                    callback_data="challenge_info"),
            ],
        ]
    elif keyboard_type == "finish-still-active":
        keyboard = [
            [InlineKeyboardButton(
                "🎯 Текущий челлендж", 
                callback_data="challenge_next")],
            [
                InlineKeyboardButton(
                    "🏆 Топ дейли", 
                    callback_data="challenge_leaderboard"),
                InlineKeyboardButton(
                    "ℹ️ Помощь", 
                    callback_data="challenge_info"),
            ],
        ]
    elif keyboard_type == "leaderboard":
        keyboard = [
            [
                InlineKeyboardButton(
                    "📑 Главное меню дейли", 
                    callback_data="challenge_main")
            ],
        ]
    elif keyboard_type == "justamap":
        keyboard = [
            [
                InlineKeyboardButton(
                    "📑 Главное меню дейли", 
                    callback_data="challenge_main"),
                InlineKeyboardButton(
                    "⏭️ Следующая", 
                    callback_data="challenge_justamap")
            ]
        ]

    return InlineKeyboardMarkup(keyboard)
