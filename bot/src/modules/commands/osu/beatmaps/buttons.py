


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def beatmaps_keyboard(caller_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🔄 Обновить", callback_data=f"beatmaps_refresh:{caller_id}"),
            InlineKeyboardButton("⭐️ Посчитать меня", callback_data=f"beatmaps_count_me:{caller_id}"),
        ],
        [
            InlineKeyboardButton("посмотреть статистику карт из...", callback_data=f"beatmaps_refresh:{caller_id}"),
        ],
        [
            InlineKeyboardButton("📊 200 карт", callback_data=f"beatmaps_stats_200:{caller_id}"),
            InlineKeyboardButton("🔹 top-100 pp", callback_data=f"beatmaps_stats_1_100:{caller_id}"),
            InlineKeyboardButton("🔸 most played", callback_data=f"beatmaps_stats_101_200:{caller_id}"),            
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
