


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def get_keyboard(action: str, origin_id: str, request_id: str) -> InlineKeyboardMarkup:

    if action == 'delete_message':
        keyboard = [
            [
                InlineKeyboardButton(
                    "❗️ Удалить", 
                    callback_data=f"modv:dmsg:pos:{origin_id}:{request_id}"
                ),
                InlineKeyboardButton(
                    "❎ Не удалять", 
                    callback_data=f"modv:dmsg:neg:{origin_id}:{request_id}"
                ),
            ]
        ]

    return InlineKeyboardMarkup(keyboard)
