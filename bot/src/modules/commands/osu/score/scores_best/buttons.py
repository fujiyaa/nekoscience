


from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from .....external.osu_api import get_beatmapset


async def get_keyboard(message_context, message_context_reply, 
                 origin_user_id, username_to_lookup) -> InlineKeyboardMarkup:
    keyboard = []

    map_id1 = map_title1 = mapset_id2 = None
    if message_context:
        map_id1 = message_context["metadata"].get("map_id")
        map_title1 = message_context["metadata"].get("map_title")
        mapset_id1 = message_context["metadata"].get("mapset_id")

    map_id2 = map_title2 = mapset_id2 = None
    if message_context_reply:
        map_id2 = message_context_reply["metadata"].get("map_id")
        map_title2 = message_context_reply["metadata"].get("map_title")
        mapset_id2 = message_context_reply["metadata"].get("mapset_id")

    if map_id1 and map_id2 and map_id1 == map_id2:
        map_id2 = None
        map_title2 = None

    if map_id1:
        keyboard.append([
            InlineKeyboardButton(
                map_title1 or f"map {map_id1}",
                callback_data=f"score_best:map:{map_id1}:{origin_user_id}:{username_to_lookup}"
            )
        ])

    if map_id2:
        keyboard.append([
            InlineKeyboardButton(
                map_title2 or f"map {map_id2}",
                callback_data=f"score_best:map:{map_id2}:{origin_user_id}:{username_to_lookup}"
            )
        ])


    if mapset_id1 == mapset_id2: 
        mapset_id2 = None

    mapset_ids = []
    if mapset_id1 is not None:
        mapset_ids.append(mapset_id1)
    if mapset_id2 is not None and mapset_id2 != mapset_id1:
        mapset_ids.append(mapset_id2)

    map_titles = []
    for mapset_id in mapset_ids:
        beatmapset = await get_beatmapset(mapset_id)
        
        map_ids = [b['id'] for b in beatmapset.get("beatmaps", [])]
        map_diffs = [b['version'] for b in beatmapset.get("beatmaps", [])]
        map_title = beatmapset.get("title", "no title")

        if map_ids:
            map_titles.append((map_title, map_ids, map_diffs))

    for title, ids, diffs in map_titles:
        keyboard.append([
            InlineKeyboardButton(
                title or "Mapset",
                callback_data=f"score_best:ignore:0:{origin_user_id}:0"
            )
        ])

        # 2️⃣ Кнопки со сложностями, максимум 4 в ряд
        row = []
        for map_id, diff in zip(ids, diffs):
            row.append(
                InlineKeyboardButton(
                    diff,
                    callback_data=f"score_best:map:{map_id}:{origin_user_id}:{username_to_lookup}"
                )
            )
            if len(row) == 4:
                keyboard.append(row)
                row = []
        if row:  # остаток кнопок
            keyboard.append(row)




    keyboard.append([
        InlineKeyboardButton(
            "✖️ Отмена",
            callback_data=f"score_best:cancel:0:{origin_user_id}:{username_to_lookup}"
        )
    ])

    return InlineKeyboardMarkup(keyboard)
