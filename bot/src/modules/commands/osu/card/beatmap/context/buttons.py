


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def get_context_keyboard(
        message_context,
        message_context_reply,
        origin_user_id,
        origin_msg_id) -> InlineKeyboardMarkup:
    
    keyboard = []

    map_id1 = map_title1 = None
    if message_context:
        map_id1 = message_context["metadata"].get("map_id")
        map_title1 = message_context["metadata"].get("map_title")

    map_id2 = map_title2 = None
    if message_context_reply:
        map_id2 = message_context_reply["metadata"].get("map_id")
        map_title2 = message_context_reply["metadata"].get("map_title")

    if map_id1 and map_id2 and map_id1 == map_id2:
        map_id2 = None
        map_title2 = None

    if map_id1:
        keyboard.append([
            InlineKeyboardButton(
                map_title1 or f"{map_id1}",
                callback_data=f"card_beatmap_context:map:{map_id1}:{origin_user_id}:{origin_msg_id}"
            )
        ])

    if map_id2:
        keyboard.append([
            InlineKeyboardButton(
                map_title2 or f"{map_id2}",
                callback_data=f"card_beatmap_context:map:{map_id2}:{origin_user_id}:{origin_msg_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "✖️ Отмена",
            callback_data=f"card_beatmap_context:cancel:0:{origin_user_id}:{origin_msg_id}"
        )
    ])

    return InlineKeyboardMarkup(keyboard)