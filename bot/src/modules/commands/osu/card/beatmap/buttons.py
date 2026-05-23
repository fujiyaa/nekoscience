


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



async def get_keyboard(beatmap_id: str):     

    keyboard = [
        [
            InlineKeyboardButton(
                "📨 Получить в осу",
                callback_data=f"send_pm_with_link_to:{beatmap_id}"
            ),
            # InlineKeyboardButton(
            #     " Музыка",
            #     callback_data=f"send_music:{beatmap_id}"
            # )
        ]
    ]

    return InlineKeyboardMarkup(keyboard)
