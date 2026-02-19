


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

from ..utils.text_format import format_osu_date
from ..external.osu_api import search_beatmapsets

MAX_RESULTS = 100
SEARCH_CACHE = {}
CACHE_TTL = 30

ACTIVE_SEARCH_TASKS: dict[int, asyncio.Task] = {}



async def search_beatmapsets_cached(query_key: str, text: str, cursor: str | None):
    now = time.time()

    if query_key in SEARCH_CACHE:
        cached_data, timestamp = SEARCH_CACHE[query_key]
        if now - timestamp < CACHE_TTL:
            return cached_data

    result = await search_beatmapsets(text, cursor)

    SEARCH_CACHE[query_key] = (result, now)
    return result


async def inline_osu_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.inline_query
        q = query.query.strip()
        cursor = query.offset or None

        help_text = 'Нужна помощь? Используй команду <code>/help inline</code>'

        if not q:
            results_help = []

            results_help.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="☑️ продолжай вводить команду...",
                    description="не нажимай на кнопки этого меню",
                    input_message_content=InputTextMessageContent(
                        help_text,
                        parse_mode='HTML',
                    )
                )
            )

            results_help.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="map 〰️ поиск карт по названию",
                    description="пример: @fujiyaosubot map KOTOKO",
                    input_message_content=InputTextMessageContent(
                        help_text,
                        parse_mode='HTML',
                    )
                )
            )

            await query.answer(
                results=results_help,
                cache_time=1,
                is_personal=True
            )
            return

        if not q.lower().startswith("map ") and len(q)>3:
            result = InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"❗️команды {q.lower()} не существует",
                description="есть такая команда: map",
                input_message_content=InputTextMessageContent(
                    help_text,
                    parse_mode='HTML',
                )
            )

            await query.answer(
                results=[result],
                cache_time=1,
                is_personal=True
            )
            return
        
        if q.lower() == ("map") or q.lower() == ("map "):
            result = InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"☑️ теперь вводи название карты...",
                description="🎶",
                input_message_content=InputTextMessageContent(
                    "Нужна помощь? Используй команду <code>/help inline</code>",
                    parse_mode='HTML',
                )
            )

            await query.answer(
                results=[result],
                cache_time=1,
                is_personal=True
            )
            return

        search_term = q[4:].strip()
        if not search_term:
            await query.answer([], cache_time=1, is_personal=True)
            return

        user_id = query.from_user.id

        old_task = ACTIVE_SEARCH_TASKS.get(user_id)
        if old_task and not old_task.done():
            old_task.cancel()

        task = asyncio.create_task(
            search_beatmapsets_cached(q, search_term, cursor)
        )

        ACTIVE_SEARCH_TASKS[user_id] = task

        try:
            beatmapsets = await task
        except asyncio.CancelledError:
            return

        if ACTIVE_SEARCH_TASKS.get(user_id) is not task:
            return

        ACTIVE_SEARCH_TASKS.pop(user_id, None)

        if not beatmapsets:
            await query.answer([], cache_time=1, is_personal=True)
            return

        total = beatmapsets.get('total', 0)
        next_cursor = beatmapsets.get('cursor_string') if total > MAX_RESULTS else None

        results = []

        for beatmapset in beatmapsets.get('beatmapsets', [])[:MAX_RESULTS]:

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
                b.get('difficulty_rating')
                for b in beatmaps
                if b.get('difficulty_rating') is not None
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

            mapset_id = beatmapset.get('id')
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
                    ),
                ]
            ])

            username = query.from_user.username or "user"

            mapset_text = (
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
                        message_text=mapset_text,
                        parse_mode='HTML',
                        link_preview_options=link_preview
                    ),
                    reply_markup=kb,
                    thumbnail_url=cover_url
                )
            )

        if not results:
            results.append(
                InlineQueryResultArticle(
                    id="notfound",
                    title="Ничего не найдено",
                    input_message_content=InputTextMessageContent(
                        f"{search_term} — нет результатов"
                    )
                )
            )

        await query.answer(
            results=results,
            cache_time=1,
            is_personal=True,
            next_offset=next_cursor or ""
        )

    except Exception:
        traceback.print_exc()
