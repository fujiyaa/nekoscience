


import asyncio
import traceback
import html

from telegram import Update, LinkPreviewOptions, MessageEntity
from telegram.ext import ContextTypes

from ....actions.messages import safe_send_message
from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....systems.auth import check_osu_verified, get_osu_id
from ....external.localapi import read_file_neko, insert_to_file_neko
from ....systems.cooldowns import check_user_cooldown
from ....actions.messages import safe_send_message
from ....external.osu_api import get_osu_token
from ....actions.messages import safe_send_message
from ....external.osu_http import fetch_txt_beatmaps
from ....external.osu_api import get_osu_token, get_beatmap, get_score_by_id
from .buttons import *
from .json_schema import construct_user
from .options import *
from .rank import *
from .match import *

from config import COOLDOWN_UNRANKED_COMMANDS
from config import OSU_URL_REGEX

MAX_ATTEMPTS = 2



async def start_unranked_game(update, context):
    await log_all_update(update)
    asyncio.create_task(unranked_game(update, context))

async def unranked_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if not await filter_other_topics(update, context): 
    #     return

    user_id = str(update.effective_user.id)
    can_run = await check_user_cooldown(
        command_name="unranked_game_main",
        user_id=user_id,
        cooldown_seconds=COOLDOWN_UNRANKED_COMMANDS,
        update=update,
        context=context        
    )
    if not can_run or update.effective_user.username is None:
        return
    else:    
        tg_id = update.effective_user.id 
        tg_name = update.effective_user.username

    osu_name = await check_osu_verified(user_id)
    if not osu_name:
        await safe_send_message(
            update, "⚠ Не сохранен ник, он нужен для игры! Нажми и авторизуйся: /name", 
            parse_mode="Markdown")
        return
    
    osu_id = await get_osu_id(user_id)
    if osu_id: 
        osu_id = str(osu_id) 
    else: 
        await safe_send_message(
            update, "⚠ Что-то не так с авторизацией, попробуй еще раз вот это: /name", 
            parse_mode="Markdown")
        return
    
    link_preview = LinkPreviewOptions(
        url=BANNER_OPTIONS[0],
        is_disabled=False,
        prefer_small_media=False,
        prefer_large_media=True,
        show_above_text=True
    )

    message_text = update.message.text.strip()
    result = parse_osu_url(message_text)

    # режим главного меню когда нет ссылок
    if result is None:
        response = await read_file_neko(d_file)
        data = response.get("current", {})

        if osu_id not in data:
            data[osu_id] = construct_user(
                osu_id, 
                osu_name, 
                tg_id,
                tg_name,
            )
            await insert_to_file_neko(d_file, data)

        user = data[osu_id]
        config = user.get("config")
        points = user.get("points")
        current = points.get("current")
        active_matches = user.get("active_matches")
        rank = get_player_rank(data, osu_id)

        rank = get_player_rank(data, osu_id)
        rating_text = f"<b>{osu_name}</b> <i>@{tg_name}</i>   <b>🏆{current}</b>  (#{rank})"
        text = f"""
{rating_text}
<code>- игр в процессе: {len(active_matches)}</code>
<code>- мин/макс ELO: {points.get('min')}/{points.get('max')}</code>

{MAIN_MENU_TEXT}
"""

        reply_markup = get_keyboard(
            "main-menu", 
            config, 
            owner_id=tg_id
        )

        await update.message.reply_text(
            text = text,
            reply_markup = reply_markup,
            parse_mode = "HTML",
            link_preview_options=link_preview
        )
        
        return
    
    if result["sent_type"] == 'score':
        try:
            token = await get_osu_token()

            cached_entry =  await get_score_by_id(result["sent_id"], token, override = True)

            if not cached_entry:
                await safe_send_message(update, "❌ Не удалось загрузить скор", parse_mode="Markdown")
                return
                        

            map_id = cached_entry.get('map').get('beatmap_id')
            map_full = cached_entry.get('map').get('beatmap_full')
            
            sent_mods = str(((cached_entry.get('osu_score') or {}).get('mods')) or "")
            
            sent_score_user_id = cached_entry.get('osu_score').get('user_id')
                
        except Exception:
            traceback.print_exc()
            await safe_send_message(update, "❌ Ошибка", parse_mode="Markdown")
    else:
        try:
            token = await get_osu_token()

            maps_ids = []
            maps_ids.append(result["sent_id"])

            results, failed = await fetch_txt_beatmaps(maps_ids)

            token = await get_osu_token()
            map_data = await get_beatmap(result["sent_id"], token)
            
            beatmap = map_data
            beatmapset = map_data.get("beatmapset", {})

            map_id = map_data.get('id')
            map_full = f"{beatmapset.get('artist', '')} - {beatmapset.get('title', '')} [{beatmap.get('version', '')}]"

            sent_mods = "" 

        except Exception:
            traceback.print_exc()
            await safe_send_message(update, "❌ Ошибка", parse_mode="Markdown")
    
    
    try:    
        if result["sent_type"] == 'score':
            if str(sent_score_user_id) != str(osu_id):
                await update.message.reply_text(
                    "🆔 Игроков (у скора и у тебя) не совпадают, что довольно печально! Мне обязательно нужен твой собственный скор.",
                    parse_mode="HTML",
                )
                return
        
        response = await read_file_neko(d_file)
        data = response.get("current", {})

        if osu_id not in data:
            data[osu_id] = construct_user(
                osu_id, 
                osu_name, 
                tg_id,
                tg_name,
            )
            await insert_to_file_neko(d_file, data)

        user = data[osu_id]
        active_matches = user.get("active_matches")
        config = user.get("config")
        points = user.get("points")
        current = points.get("current")
        rank = get_player_rank(data, osu_id)

        creation_text = f"<b>Создание раунда</b>"
        rating_text = f"<b>{osu_name}</b> (@{tg_name})   <b>🏆{current}</b>  <i>(#{rank})</i>"
        difficulty_text = f'<a href="https://osu.ppy.sh/b/{map_id}">{html.escape(map_full)} 🔗</a>'
        
        if len(active_matches) < 20:

            intake_new = {
                "sent_type": result['sent_type'],
                "sent_id": result['sent_id'],
                "map_full": html.escape(map_full),
                "sent_mods": sent_mods,
                "map_id": map_id,
                "temp_rank": rank
            }

            if result['sent_type'] == 'map':
                config['source'] = 1

            data[osu_id] = construct_user(
                osu_id, 
                osu_name, 
                tg_id,
                tg_name,
                points=points,
                config=config,
                intake=intake_new,                
                active_matches=active_matches,
            )
            await insert_to_file_neko(d_file, data)

            text = f"{rating_text}\n\n{creation_text}: {difficulty_text}"
            reply_markup = get_keyboard("main", config, intake_new, owner_id=tg_id)

        # тут должно быть автозавершение обязательно
        else:                
            response = await read_file_neko(m_file)

            matches = response.get("current", {})

            matches_list = get_user_matches(
                matches,
                active_matches
            )

            text = "\n".join(matches_list)

            def tg_len(text: str) -> int:
                return len(text.encode("utf-16-le")) // 2
            
            entities = [
                MessageEntity(
                    type="expandable_blockquote",
                    offset=0,                     
                    length=tg_len(text)    
                )
            ]

            reply_markup = get_active_matches_keyboard(
                active_matches,
                matches,
                owner_id=tg_id
            )

            await update.message.reply_text(
                text=f"{text}\n{MAIN_MENU_MYACTIVE_LIMIT}",
                reply_markup=reply_markup,
                link_preview_options=link_preview,
                entities=entities
            )

            return

        try:
            return await update.message.reply_text(
                text,
                parse_mode="HTML",
                link_preview_options=link_preview,
                reply_markup=reply_markup
            ) 
        except:
            await safe_send_message(
                update,
                text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

        return
    except Exception:
        traceback.print_exc()

def parse_osu_url(url: str) -> dict | None:
    match = OSU_URL_REGEX.search(url.strip())

    if not match:
        return None

    groups = match.groupdict()

    if groups.get("score_id"):
        return {
            "sent_type": "score",
            "sent_id": int(groups["score_id"])
        }

    if groups.get("map_id1"):
        return {
            "sent_type": "map",
            "sent_id": int(groups["map_id1"])
        }

    if groups.get("map_id2"):
        return {
            "sent_type": "map",
            "sent_id": int(groups["map_id2"])
        }

    if groups.get("set_id"):
        return {
            "sent_type": "map",
            "sent_id": int(groups["set_id"])
        }

    return None