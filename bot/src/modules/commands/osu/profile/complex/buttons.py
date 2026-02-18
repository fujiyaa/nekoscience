


from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .....systems.auth import check_osu_verified



async def get_keyboard(
    message_context,
    message_context_reply, 
    current_username,
    origin_user_id,
    action: str
) -> InlineKeyboardMarkup:
    
    keyboard = []

    osu_username1, osu_username2 = None, None
    origin_username1, origin_username2 = None, None
    mapper_username1, mapper_username2 = None, None
    map_title1, map_title2 = None, None


    if message_context:
        osu_username1 = message_context["metadata"].get("profile_player_username")

        origin_username1 = message_context["metadata"].get("origin_call_user_id")
        if origin_username1:
            origin_username1 = await check_osu_verified(str(origin_username1))

        mapper_username1 = message_context["metadata"].get("mapper_username")
        map_title1 = message_context["metadata"].get("map_title")


    if message_context_reply:
        osu_username2 = message_context_reply["metadata"].get("profile_player_username")

        origin_username2 = message_context_reply["metadata"].get("origin_call_user_id")
        if origin_username2:
            origin_username2 = await check_osu_verified(str(origin_username2))

        mapper_username2 = message_context_reply["metadata"].get("mapper_username")
        map_title2 = message_context_reply["metadata"].get("map_title")


    def _filter(uns):
        seen = set()
        for i, name in enumerate(uns):
            if name in seen:
                uns[i] = None
            elif name:
                seen.add(name)
        return uns
    

    usernames = [osu_username1, osu_username2, current_username, origin_username1, origin_username2]
    mappers = [mapper_username1, mapper_username2]

    usernames = _filter(usernames)
    mappers = _filter(mappers)

    osu_username1, osu_username2, current_username, origin_username1, origin_username2 = usernames
    mapper_username1, mapper_username2 = mappers

    good_action = f"ctx1:{action}:u"

    if current_username:
        keyboard.append([
            InlineKeyboardButton(
                f"{current_username} (свой профиль)",
                callback_data=f"{good_action}:{current_username}:{origin_user_id}"
            )
        ])

    if origin_username1:
        keyboard.append([
            InlineKeyboardButton(
                f"{origin_username1} (запрос команды)",
                callback_data=f"{good_action}:{origin_username1}:{origin_user_id}"
            )
        ])

    if origin_username2:
        keyboard.append([
            InlineKeyboardButton(
                f"{origin_username2} (запрос команды)",
                callback_data=f"{good_action}:{origin_username2}:{origin_user_id}"
            )
        ])

    if osu_username1:
        keyboard.append([
            InlineKeyboardButton(
                f"{osu_username1} (последний профиль)",
                callback_data=f"{good_action}:{osu_username1}:{origin_user_id}"
            )
        ])

    if osu_username2:
        keyboard.append([
            InlineKeyboardButton(
                f"{osu_username2} (последний профиль)",
                callback_data=f"{good_action}:{osu_username2}:{origin_user_id}"
            )
        ])

    if mapper_username1:
        keyboard.append([
            InlineKeyboardButton(
                f"{mapper_username1} (маппер {map_title1})",
                callback_data=f"{good_action}:{mapper_username1}:{origin_user_id}"
            )
        ])

    if mapper_username2:
        keyboard.append([
            InlineKeyboardButton(
                f"{mapper_username2} (маппер {map_title2})",
                callback_data=f"{good_action}:{mapper_username2}:{origin_user_id}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "✖️ Отмена",
            callback_data=f"ctx1:action:c:username:{origin_user_id}"
        )
    ])

    return InlineKeyboardMarkup(keyboard)
