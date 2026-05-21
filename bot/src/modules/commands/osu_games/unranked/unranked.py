


from contextlib import asynccontextmanager
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
from ....external.osu_http import fetch_txt_beatmaps
from ....external.osu_api import get_beatmap, get_score_by_id
from ....actions.context import get_message_context
from .buttons import *
from .json_schema import construct_user
from .options import *
from .rank import *
from .match import *
from .locks import GLOBAL_LOCK
from .actions_log import *

from config import SUPPORT_STUB, MAX_TEXT_LENGTH
from config import COOLDOWN_UNRANKED_COMMANDS
from config import OSU_URL_REGEX

MAX_ATTEMPTS = 2

class StopTransaction(Exception):
    def __init__(self, send=None):
        self.send = send

@asynccontextmanager
async def transaction():
    async with GLOBAL_LOCK:
        yield

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
    try:
        if not can_run: return

        message_id = update.effective_message.id
        tg_id = update.effective_user.id 
        tg_name = update.effective_user.username

        if tg_name is None or tg_id is None or message_id is None:
            raise StopTransaction(                
                send={
                    "method": "reply_text",
                    "kwargs":{
                        "text": "<code>⚠ Что-то не так. Возможно, у тебя скрыт юзернейм, либо у бота недостаточно прав для чтения сообщений</code>",
                        "parse_mode": "HTML",
                        "reply_markup": None
                    }
                }
            )


        osu_name = await check_osu_verified(user_id)

        if not osu_name:
            raise StopTransaction(                
                send={
                    "method": "reply_text",
                    "kwargs":{
                        "text": "<code>⚠ Что-то не так с авторизацией, попробуй еще раз вот это:</code> /name",
                        "parse_mode": "HTML",
                        "reply_markup": None
                    }
                }
            )
        
        osu_id = await get_osu_id(user_id)
        if osu_id: 
            osu_id = str(osu_id) 
        else: 
            raise StopTransaction(                
                send={
                    "method": "reply_text",
                    "kwargs":{
                        "text": "<code>⚠ Что-то не так с авторизацией, попробуй еще раз вот это:</code> /name",
                        "parse_mode": "HTML",
                        "reply_markup": None
                    }
                }
            )
        
        link_preview = LinkPreviewOptions(
            url=BANNER_OPTIONS[0],
            is_disabled=False,
            prefer_small_media=False,
            prefer_large_media=True,
            show_above_text=True
        )

        message_text = update.message.text.strip()
        result = parse_osu_url(message_text)

        # когда нет ссылок проверить контекст
        if result is None:

            context_result = None

            try:
                context_score_ok = context_map_ok = False
                DA_values = None
                message_context = get_message_context(update, reply=False)

                # если нет то и не важно
                if message_context:
                    context_score_id = None

                    context_score_id = message_context["metadata"].get("score_id")
                    
                    # может быть есть скор id
                    if context_score_id:

                        cached_entry =  await get_score_by_id(context_score_id)

                        if not cached_entry:
                            logger.warning(f"[context parse] cached_entry, id {context_score_id} failed")
                        
                        else:
                            map_id = cached_entry.get('map').get('beatmap_id')
                            map_full = cached_entry.get('map').get('beatmap_full')
                            
                            sent_mods = str(((cached_entry.get('osu_score') or {}).get('mods')) or "")
                            
                            sent_score_user_id = cached_entry.get('osu_score').get('user_id')
                            sent_score_failed = bool(cached_entry.get('osu_score').get('failed'))

                            if str(sent_score_user_id) == str(osu_id):
                                if not sent_score_failed:
                                    context_score_ok = True

                                    DA_values = cached_entry.get('lazer_data', {}).get('DA_values')
                                    if DA_values == {}: DA_values = None
                                
                    # или может быть есть id карты
                    if not context_score_id or (context_score_id and not context_score_ok):
                        context_map_id = None

                        context_map_id = message_context["metadata"].get("map_id")

                        if context_map_id:
                            maps_ids = []
                            maps_ids.append(context_map_id)

                            results, failed = await fetch_txt_beatmaps(maps_ids)

                            map_data = await get_beatmap(context_map_id)
                            
                            beatmap = map_data
                            beatmapset = map_data.get("beatmapset", {})

                            map_id = map_data.get('id')
                            map_full = f"{beatmapset.get('artist', '')} - {beatmapset.get('title', '')} [{beatmap.get('version', '')}]"

                            sent_mods = ""

                            if map_id: context_map_ok = True

                    if context_score_ok or context_map_ok:
                        if context_score_ok:
                            context_result = {
                                "sent_type": "score",
                                "sent_id": int(context_score_id)
                            }
                        else:
                            context_result = {
                                "sent_type": "map",
                                "sent_id": int(map_id)
                            }

                        async with transaction():
                
                            response = await read_file_neko(d_file)
                            data = response.get("current", {})

                            if osu_id not in data:
                                logger.info(f"[osu_id not in data 1] data: {data}")

                                data[osu_id] = construct_user(
                                    osu_id, 
                                    osu_name, 
                                    tg_id,
                                    tg_name,
                                )
                                await insert_to_file_neko(d_file, data)

                                logger.info(f"[user {osu_id}] added new user")

                            user = data[osu_id]
                            active_matches = user.get("active_matches")
                            config = user.get("config")
                            points = user.get("points")
                            current = points.get("current")
                            rank = get_player_rank(data, osu_id)
                            meta = user.get("meta")
                            

                            intake_new = {
                                "sent_type": context_result['sent_type'],
                                "sent_id": context_result['sent_id'],
                                "map_full": html.escape(map_full),
                                "sent_mods": sent_mods,
                                "map_id": map_id,
                                "temp_rank": rank,
                                "DA_values": DA_values,
                            }

                            if context_result['sent_type'] == 'map':
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
                                meta=meta
                            )
                            await insert_to_file_neko(d_file, data)

                            logger.info(f"[user {osu_id}] updated with new intake, type: {context_result['sent_type']}")

            except Exception as e:
                logger.warning(f"[context parse] failed: {e}")                        
                pass

            async with transaction():
                response = await read_file_neko(d_file)
                data = response.get("current", {})

                if osu_id not in data:
                    logger.info(f"[osu_id not in data 2] data: {data}")

                    data[osu_id] = construct_user(
                        osu_id, 
                        osu_name, 
                        tg_id,
                        tg_name,
                    )
                    await insert_to_file_neko(d_file, data)

                    logger.info(f"[user {osu_id}] added new user")

                user = data[osu_id]
                config = user.get("config")
                points = user.get("points")
                meta = user.get("meta", {})
                current = points.get("current")
                active_matches = user.get("active_matches")

                skip = meta.get("skip_tutorial")
                if skip:

                    rank = get_player_rank(data, osu_id)

                    rating_text = f"<b>{osu_name}</b> <i>@{tg_name}</i>   <b>🏆{current}</b>  (#{rank})"
                    intake_text = "<code>- создание: нет нового контекста</code>"
                    if context_result:
                        intake_text = f"<code>+ создание: из {context_result['sent_type']} {context_result['sent_id']}</code>"
                    
                    text = f"""
{rating_text}
<code>- Elo макс: {points.get('max')}</code>
<code>- игр в процессе: {len(active_matches)}</code>
{intake_text}
            """                 
                    

                    reply_markup = get_keyboard(
                        "main-menu", 
                        config, 
                        owner_id=tg_id
                    )

                    raise StopTransaction(                
                        send={
                            "method": "reply_text",
                            "kwargs":{
                                "text": text,
                                "parse_mode": "HTML",
                                "reply_markup": reply_markup,
                                "link_preview_options": link_preview
                            }
                        }
                    )
                else:
                    page = 0
                    reply_markup = get_tutorial_keyboard(
                        page=page,
                        owner_id=tg_id
                    )

                    raise StopTransaction(                
                        send={
                            "method": "reply_text",
                            "kwargs":{
                                "text": f"{UNRANKED_TUTORIAL[page]}",
                                "parse_mode": "HTML",
                                "reply_markup": reply_markup,
                                "link_preview_options": link_preview
                            }
                        }
                    )
        else:
            if result["sent_type"] == 'score':            

                cached_entry =  await get_score_by_id(result["sent_id"])

                if not cached_entry:
                    await safe_send_message(update, "❌ Не удалось загрузить скор", parse_mode="Markdown")
                    return                        

                map_id = cached_entry.get('map').get('beatmap_id')
                map_full = cached_entry.get('map').get('beatmap_full')
                
                sent_mods = str(((cached_entry.get('osu_score') or {}).get('mods')) or "")
                
                sent_score_user_id = cached_entry.get('osu_score').get('user_id')
                sent_score_failed = bool(cached_entry.get('osu_score').get('failed'))

                sent_client_lazer = bool(cached_entry.get('state').get('lazer'))
                
                DA_values = cached_entry.get('lazer_data', {}).get('DA_values')
                if DA_values == {}: DA_values = None
                        
            else:
                maps_ids = []
                maps_ids.append(result["sent_id"])

                results, failed = await fetch_txt_beatmaps(maps_ids)

                map_data = await get_beatmap(result["sent_id"])
                
                beatmap = map_data
                beatmapset = map_data.get("beatmapset", {})

                map_id = map_data.get('id')
                map_full = f"{beatmapset.get('artist', '')} - {beatmapset.get('title', '')} [{beatmap.get('version', '')}]"

                sent_mods = ""
                DA_values = None

                if result["sent_type"] == 'score':
                    if str(sent_score_user_id) != str(osu_id):
                        raise StopTransaction(                
                            send={
                                "method": "reply_text",
                                "kwargs":{
                                    "text": "<code>🆔 Игроков (у скора и у тебя) не совпадают, что довольно печально! Мне обязательно нужен твой собственный скор</code>",
                                    "parse_mode": "HTML"
                                }
                            }
                        )
                    if sent_score_failed:
                        raise StopTransaction(                
                            send={
                                "method": "reply_text",
                                "kwargs":{
                                    "text": "<code>❌ Кажется этот скор с фейлом, мне нужен твой скор с прохождением всей карты!</code>",
                                    "parse_mode": "HTML"
                                }
                            }
                        )                                   
                    
                
                async with transaction():
                
                    response = await read_file_neko(d_file)
                    data = response.get("current", {})

                    if osu_id not in data:
                        logger.info(f"[osu_id not in data 3] data: {data}")

                        data[osu_id] = construct_user(
                            osu_id, 
                            osu_name, 
                            tg_id,
                            tg_name,
                        )
                        await insert_to_file_neko(d_file, data)

                        logger.info(f"[user {osu_id}] added new user")

                    user = data[osu_id]
                    active_matches = user.get("active_matches")
                    config = user.get("config")
                    points = user.get("points")
                    current = points.get("current")
                    rank = get_player_rank(data, osu_id)
                    meta = user.get("meta")

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
                            "temp_rank": rank,
                            "DA_values": DA_values,
                        }

                        
                        # пресет конфига из интейка перед тем как создать меню create
                        if result['sent_type'] == 'map':
                            config['source'] = 1
                        try:
                            if config.get('source') == 0:

                                if sent_client_lazer:
                                    config['crossclient'] = 0
                                else: 
                                    config['crossclient'] = 1
                        except:
                            logger.warning(f"[user {osu_id}] has config source-0 and sent_client_x errored out (pass)")
                            pass


                        data[osu_id] = construct_user(
                            osu_id, 
                            osu_name, 
                            tg_id,
                            tg_name,
                            points=points,
                            config=config,
                            intake=intake_new,                
                            active_matches=active_matches,
                            meta=meta
                        )
                        await insert_to_file_neko(d_file, data)

                        logger.info(f"[user {osu_id}] constructing again with inatke_new")
                        logger.info(f"[user {osu_id}] updated with new intake, type: {result['sent_type']}")

                        text = f"{rating_text}\n\n{creation_text}: {difficulty_text}"
                        reply_markup = get_keyboard("main", config, intake_new, owner_id=tg_id)

                        raise StopTransaction(                
                            send={
                                "method": "reply_text",
                                "kwargs":{
                                    "text": text,
                                    "reply_markup": reply_markup,
                                    "link_preview_options": link_preview,
                                    "parse_mode": "HTML"
                                }
                            }
                        )
                   
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

                        raise StopTransaction(                
                            send={
                                "method": "reply_text",
                                "kwargs":{
                                    "text": f"{text}\n{MAIN_MENU_MYACTIVE_LIMIT}",
                                    "reply_markup": reply_markup,
                                    "link_preview_options": link_preview,
                                    "entities": entities
                                }
                            }
                        )
                   
    except StopTransaction as e:

        if e.send:
            method = e.send["method"]
            kwargs = e.send["kwargs"]

            if method == "reply_text":
                await update.message.reply_text(**kwargs)

            else:
                logger.warning(f"[unknown] method in StopTransaction")

    except Exception:
        error_details = traceback.format_exc()
        full_text = f"{error_details}\n\n{SUPPORT_STUB}"

        try:
            for i in range(0, len(full_text), MAX_TEXT_LENGTH):
                chunk = full_text[i:i + MAX_TEXT_LENGTH]
                await context.bot.send_message(
                    chat_id=update.message.from_user.id,
                    text=chunk
                )
        except Exception as e:
            print(e)

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