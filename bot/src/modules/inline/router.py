


import time
import traceback
import uuid
import asyncio

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LinkPreviewOptions
)
from telegram.ext import ContextTypes

from ..utils.text_format import (
    format_osu_date, 
    country_code_to_flag
)
from ..external.osu_api import (
    search_beatmapsets,
    search_profiles
)

MAX_RESULTS = 100
CACHE_TTL = 30

SEARCH_CACHE = {}
ACTIVE_SEARCH_TASKS: dict[int, asyncio.Task] = {}



async def search_beatmapsets_cached(query_key: str, text: str, cursor: str | None):
    now = time.time()

    cache_key = f"{query_key}:{cursor or 'first'}"

    if cache_key in SEARCH_CACHE:
        cached_data, timestamp = SEARCH_CACHE[cache_key]
        if now - timestamp < CACHE_TTL:
            return cached_data

    result = await search_beatmapsets(text, cursor)
    SEARCH_CACHE[cache_key] = (result, now)
    return result


async def search_profiles_cached(query_key: str, text: str, page: int):
    now = time.time()
    page = int(page)

    cache_key = f"{query_key}:{page}"

    if cache_key in SEARCH_CACHE:
        cached_data, timestamp = SEARCH_CACHE[cache_key]
        if now - timestamp < CACHE_TTL:
            return cached_data

    result = await search_profiles(text, page)
    if not result or "user" not in result:
        result = {"user": {"data": [], "total": 0}}

    SEARCH_CACHE[cache_key] = (result, now)
    return result


def format_map_results(data, query, search_term, seen_ids: set | None = None):
    results = []

    if seen_ids is None:
        seen_ids = set()

    next_cursor = data.get("cursor_string")

    for beatmapset in data.get("beatmapsets", []):

        mapset_id = beatmapset.get("id")

        if mapset_id in seen_ids:
            print('removed duplicate: id', mapset_id)
            continue

        seen_ids.add(mapset_id)

        title = beatmapset.get("title", "Unknown")
        artist = beatmapset.get("artist", "Unknown")
        creator = beatmapset.get("creator", "Unknown")
        status = beatmapset.get("status", "Unknown").capitalize()

        bpm = beatmapset.get("bpm")
        bpm_text = f"{float(bpm):.1f} bpm" if bpm else "?"

        last_updated = format_osu_date(
            beatmapset.get("last_updated", "?"),
            today=False
        )

        beatmaps = beatmapset.get("beatmaps", [])
        difficulty_ratings = [
            b.get("difficulty_rating")
            for b in beatmaps
            if b.get("difficulty_rating") is not None
        ]

        diff_text = ""
        if difficulty_ratings:
            min_diff = min(difficulty_ratings)
            max_diff = max(difficulty_ratings)
            if abs(max_diff - min_diff) < 0.01:
                diff_text = f"{max_diff:.2f}★"
            else:
                diff_text = f"{min_diff:.2f} - {max_diff:.2f}★"

        status_emoji = {
            "Approved": "🔺",
            "Ranked": "🔺",
            "Loved": "🔹",
            "Pending": "🔸"
        }.get(status, "")

        mapset_url = f"https://osu.ppy.sh/beatmapsets/{mapset_id}"

        cover_url = (
            beatmapset.get("covers", {}).get("cover")
            or "https://osu.ppy.sh/images/layout/card-404.png"
        )

        direct_url = f"https://myangelfujiya.ru/darkness/direct?id={mapset_id}"
        beatconnect_url = f"https://beatconnect.io/b/{mapset_id}"

        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔗 Direct", url=direct_url),
                InlineKeyboardButton("🍥 Mirror", url=beatconnect_url),
                InlineKeyboardButton(
                    "🔄 Поиск",
                    switch_inline_query_current_chat=f"map {search_term}"
                )
            ]
        ])

        username = query.from_user.username or "user"

        message_text = (
            f"@{username}  •  "
            f"<a href=\"{mapset_url}\"><b>Mapset</b></a>  •  "
            f"id<code>{mapset_id}</code>"
        )

        link_preview = LinkPreviewOptions(
            url=mapset_url,
            is_disabled=False,
            prefer_large_media=True,
            show_above_text=True
        )

        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"{artist} - {title}",
                description=(
                    f"{status_emoji} {status} • "
                    f"{diff_text} • "
                    f"{bpm_text} • "
                    f"mapper: {creator} • "
                    f"{last_updated}"
                ),
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="HTML",
                    link_preview_options=link_preview
                ),
                reply_markup=kb,
                thumbnail_url=cover_url
            )
        )

        if len(results) >= MAX_RESULTS:
            break

    return results, next_cursor


def format_profile_results(data, query, search_term, page):
    results = []

    users_data = data.get("user", {})
    users = users_data.get("data", [])
    total = users_data.get("total", 0)

    for profile in users[:MAX_RESULTS]:
        username_text = profile.get("username")
        user_id = profile.get("id")
        country = profile.get("country_code", "?")
        flag = f'{country_code_to_flag(country)} {country}'
        avatar_url = profile.get("avatar_url", "")
        is_online = bool(profile.get("is_online") or False)
        is_supporter = bool(profile.get("is_supporter") or False) 
        pm_friends_only = bool(profile.get("pm_friends_only", True))

        buttons = []

        online_text, supporter_text, pm_friends_only_text = '💤 Offline', '', ''
        if is_online:
            online_text = '📶 Online'

        if is_supporter:
            supporter_text = '  •  💕 Supporter'

        if not pm_friends_only:
            pm_friends_only_text = '  •  ✉️ DMs'
            buttons.append(
                InlineKeyboardButton(
                    "✉️ Open DMs", 
                    url=f'https://osu.ppy.sh/home/messages/users/{user_id}'
                )
            )

        profile_url = f"https://osu.ppy.sh/users/{user_id}"

        username = query.from_user.username or "user"

        message_text = (
            f"@{username}  •  "
            f"<a href=\"{profile_url}\"><b>Profile</b></a>  •  "
            f"id<code>{user_id}</code>"
        )

        buttons.append(
            InlineKeyboardButton(
                "🔄 Поиск",
                switch_inline_query_current_chat=f"user {search_term}"
            )
        )

        kb = InlineKeyboardMarkup([buttons])

        link_preview = LinkPreviewOptions(
            url=profile_url,
            is_disabled=False,
            prefer_large_media=True,
            show_above_text=True
        )

        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f'{username_text}',
                description=f"{flag}  •  {online_text}{supporter_text}{pm_friends_only_text}",                
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                    parse_mode="HTML",
                    link_preview_options=link_preview
                ),
                reply_markup=kb,
                thumbnail_url=avatar_url
            )
        )

    if users or (page == 1 and total == 0):
        next_offset = str(page + 1) if users else ""
    else:
        next_offset = ""

    return results, next_offset

COMMANDS = {
    "map": {
        "search_func": search_beatmapsets_cached,
        "formatter": format_map_results,
        "pagination": "cursor"
    },
    "user": {
        "search_func": search_profiles_cached,
        "formatter": format_profile_results,
        "pagination": "page"
    }
}


async def inline_osu_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.inline_query
        q = query.query.strip()
        help_text = 'Нужна помощь? Используй команду <code>/help inline</code>'

        user_id = query.from_user.id

        if not q:
            results_help = [
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="☑️ продолжай вводить команду...",
                    description="не нажимай на кнопки этого меню",
                    input_message_content=InputTextMessageContent(help_text, parse_mode='HTML')
                ),
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="map 〰️ поиск карт по названию",
                    description="пример: @WeakoBot MAP kotoko",
                    input_message_content=InputTextMessageContent(help_text, parse_mode='HTML')
                ),
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="user 〰️ поиск профиля пользователя",
                    description="пример: @WeakoBot USER vaxei",
                    input_message_content=InputTextMessageContent(help_text, parse_mode='HTML')
                )
            ]
            await query.answer(results=results_help, cache_time=1, is_personal=True)
            return

        parts = q.split(" ", 1)
        command = parts[0].lower()
        search_term = parts[1].strip() if len(parts) > 1 else ""

        if command not in COMMANDS:
            await query.answer(
                results=[InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"❗️команды {command} не существует",
                    description="команды: map, user",
                    input_message_content=InputTextMessageContent(help_text, parse_mode='HTML')
                )],
                cache_time=1,
                is_personal=True
            )
            return

        if not search_term:
            await query.answer(
                results=[InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"☑️ {command}, вводи текст для поиска...",
                    description="🎯",
                    input_message_content=InputTextMessageContent(help_text, parse_mode='HTML')
                )],
                cache_time=1,
                is_personal=True
            )
            return

        pagination_type = COMMANDS[command]["pagination"]
        if pagination_type == "cursor":
            offset = query.offset or None
        else:
            offset = int(query.offset) if query.offset else 1

        old_task = ACTIVE_SEARCH_TASKS.get(user_id)
        if old_task and not old_task.done():
            old_task.cancel()

        search_func = COMMANDS[command]["search_func"]
        task = asyncio.create_task(search_func(q, search_term, offset))
        ACTIVE_SEARCH_TASKS[user_id] = task

        try:
            result_data = await task
        except asyncio.CancelledError:
            return

        if ACTIVE_SEARCH_TASKS.get(user_id) is not task:
            return
        ACTIVE_SEARCH_TASKS.pop(user_id, None)

        if not result_data:
            await query.answer([], cache_time=1, is_personal=True)
            return

        formatter = COMMANDS[command]["formatter"]
        if pagination_type == "cursor":
            results, next_offset = formatter(result_data, query, search_term)
        else:  # user
            results, next_offset = formatter(result_data, query, search_term, offset)

        if offset == 1 and not results:
            results = [InlineQueryResultArticle(
                id="notfound",
                title="Ничего не найдено",
                input_message_content=InputTextMessageContent(f"{search_term} — нет результатов")
            )]

        if not results:
            results = [InlineQueryResultArticle(
                id="notfound",
                title="Больше ничего не найдено",
                input_message_content=InputTextMessageContent(f"{search_term} — нет результатов")
            )]

        await query.answer(
            results=results,
            cache_time=1,
            is_personal=True,
            next_offset=next_offset or ""
        )

    except Exception:
        traceback.print_exc()