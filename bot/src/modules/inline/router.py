


import uuid
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



async def inline_osu_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    user = query.from_user
    user_id = str(user.id)
    q = query.query.strip()
    offset = query.offset
    if offset:
        cursor = offset
    else:
        cursor = None

    if not q:
        result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="@fujiyaosubot map My Love",
            description=f"Поиск карт, пример",
            input_message_content=InputTextMessageContent(
                "помощь: <code>/help inline</code>",
                parse_mode = 'HTML',
            )
        )

        await query.answer(
            results=[result],
            cache_time=0,
            is_personal=True
        )
        return


    search_term = q
    if q.lower().startswith("map "):
        search_term = search_term[4:].strip()

        if not search_term:
            return
        
        beatmapsets = await search_beatmapsets(search_term, cursor=cursor)
        total = beatmapsets.get('total', 0)
        next_cursor = beatmapsets.get('cursor_string', None) if total > 100 else None

        results = []
       
        for i, beatmapset in enumerate(beatmapsets.get('beatmapsets', [])):
            title = beatmapset.get("title", "Unknown")
            artist = beatmapset.get("artist", "Unknown")
            creator_text = f'mapper: {beatmapset.get("creator", "Unknown")}'
            # playcount_text = f'{beatmapset.get("play_count", "0")} plays'
            status = beatmapset.get("status", "Unknown").capitalize()
            bpm_text = f'{beatmapset.get("bpm", "0"):.1f} bpm'
            last_updated = format_osu_date(beatmapset.get("last_updated", "?"), today=False)

            difficulty_ratings = [b['difficulty_rating'] for b in beatmapset.get("beatmaps", [])]

            diff_text = ''
            if difficulty_ratings:
                min_diff = min(difficulty_ratings)
                max_diff = max(difficulty_ratings)

                if (max_diff - min_diff) < 0.01:
                    diff_text = f'{max_diff:.2f}*'
                else:
                    diff_text = f'{min_diff:.2f} - {max_diff:.2f}*'
            
            status_emoji = ''
            if status == 'Ranked':
                status_emoji = '🔺'
            elif status == 'Loved':
                status_emoji = '🔹'
            elif status == 'Pending':
                status_emoji = '🔸'     

            
            mapset_id = beatmapset.get('id')
            url = f"https://osu.ppy.sh/beatmapsets/{mapset_id}"
            diffs = [b.get("version", "Unknown") for b in beatmapset.get("beatmaps", [])]
            diff_str = ", ".join(diffs[:3])
            
            cover_url = beatmapset.get("covers", {}).get("cover", None)
            if not cover_url:
                cover_url = "https://osu.ppy.sh/images/layout/card-404.png"
            
            direct_url = f'https://myangelfujiya.ru/darkness/direct?id={mapset_id}'
            beatconnect_url = f'https://beatconnect.io/b/{mapset_id}'
            kb = [
                [
                    InlineKeyboardButton("🔗 Direct", url=direct_url),
                    InlineKeyboardButton("🍥 Mirror", url=beatconnect_url),
                    InlineKeyboardButton("🔄 Поиск", switch_inline_query_current_chat=f'map {search_term}'),
                ]
            ]            
            
            mapset_url = f"https://osu.ppy.sh/beatmapsets/{mapset_id}"
            mapset_text = f'@{query.from_user.username}  •  <a href="{mapset_url}"><b>Mapset</b></a>  •  id<code>{mapset_id}</code>'
            
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
                    description=f"{status_emoji} {status} • {diff_text} • {bpm_text} • {creator_text} • {last_updated}",
                    input_message_content=InputTextMessageContent(
                        message_text = mapset_text,
                        parse_mode = 'HTML',
                        link_preview_options=link_preview
                    ),
                    reply_markup=InlineKeyboardMarkup(kb),
                    thumbnail_url=cover_url
                )
            )

        if not results:
            results.append(
                InlineQueryResultArticle(
                    id="notfound",
                    title="Ничего не найдено",
                    input_message_content=InputTextMessageContent(
                        f"{search_term}' - Нет результатов"
                    )
                )
            )

        await query.answer(
            results, 
            cache_time=0,
            is_personal=True,
            next_offset=next_cursor or ""
        )
