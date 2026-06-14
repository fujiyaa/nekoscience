


import asyncio, html

from telegram import Update
from telegram.ext import ContextTypes

from .....systems.logging import log_all_update
from .utils import calculate_rank, format_text, truncate
from .buttons import get_simulate_keyboard
from .context.buttons import get_context_keyboard
from .....external.osu_http import beatmap
from .....external.localapi import get_map_stats_neko_api
from .....actions.messages import delete_user_message, delete_message_after_delay, safe_send_message
from .....actions.context import set_message_context, get_message_context
from .....external.local_skills import get_skills_by_scores_v2
from .....systems.auth import check_osu_verified, get_osu_id
from .....external.osu_api import get_top_100_scores, get_beatmap
from .....actions.rich import rich_reply

from config import OSU_MAP_REGEX, OSU_MAP_REGEX_2, PARAMS_TEMPLATE
from config import sessions_simulate



async def simulate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    map_id = None

    user_name = update.effective_user.name
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    topic_id = getattr(update.effective_message, "message_thread_id", None)

    message_text = update.message.text.strip()
    match = OSU_MAP_REGEX.search(message_text)
    match_2 = OSU_MAP_REGEX_2.search(message_text)

    if not match and not match_2:
        message_context = get_message_context(update, reply=False)
        if message_context:
            message_context_reply = get_message_context(update, reply=True)

            await safe_send_message(
                update, 
                text=f"<code>Ты хочешь посмотреть</code> <b>  карточку  </b> <code>...</code>", 
                reply_markup=await get_context_keyboard(
                    message_context, 
                    message_context_reply, 
                    origin_user_id=update.effective_user.id, 
                    origin_msg_id=update.effective_message.id
                ),
                parse_mode="HTML"
            )
    
        if not message_context:
            msg = await safe_send_message(update, text="`Нет карты в чате...`", parse_mode="Markdown")

            asyncio.create_task(delete_message_after_delay(context, msg.chat.id, msg.message_id, 10))
            asyncio.create_task(delete_user_message(update, context, delay=10))
        
        return
    
    if match is None and match_2 is None: 
            return
        
    if map_id is None:
        if match:
            beatmap_id = match.group(1) if match.group(1) else match.group(2)
        if match_2:
            beatmap_id = match_2.group(1) if match_2.group(1) else match_2.group(2)
    else:
        beatmap_id = map_id

    if user_id in sessions_simulate:
        try:
            await context.bot.delete_message(chat_id=sessions_simulate[user_id]["chat_id"],
                                             message_id=sessions_simulate[user_id]["message_id"])
        except:
            pass
        del sessions_simulate[user_id]

    
    map_id = beatmap_id

    acc_u, aim_u, speed_u = await skills(user_id)
            
    map = await get_beatmap(map_id)
    
    user_params = {k: v.copy() for k, v in PARAMS_TEMPLATE.items()}
    
    mapset = map.get('beatmapset', {})

    map_url = map.get('url')
    status = map.get('status', 'status').capitalize()
    hit_length = map.get('hit_length', 0)
    version = map.get('version', 'version')
    artist = mapset.get('artist', 'artist')
    creator = mapset.get('creator', 'creator')
    title = mapset.get('title', 'title')
    cover_url = mapset.get('covers', {}).get('slimcover@2x')

    cover_rich_block = ""
    if cover_url is not None:
        cover_rich_block = f'\n<tg-collage>\n<img src="{cover_url}"/>\n</tg-collage>\n'

    full_title = f"{artist} - {title} [{version}]"
    beatmap_escaped = html.escape(full_title)

    path, values = await beatmap(map_id)

    #neko API 
    payload = {
        "map_path": str(map_id), 
        
        "n300": None,
        "n100": None,
        "n50": None,
        "misses": None,                   
        
        "mods": str(""), 
        "combo": int(0),      
        "accuracy": float(100),    
        
        "lazer": bool(True),          
        "clock_rate": float(1.0),  

        "custom_ar": values.get("ar"),
        "custom_cs": values.get("cs"),
        "custom_hp": values.get("hp"),
        "custom_od": values.get("od"),
    }

    try:
        pp_data = await get_map_stats_neko_api(payload)

        pp = pp_data.get("pp")
        choke = pp_data.get("no_choke_pp")
        max_pp = pp_data.get("perfect_pp")

        stars = pp_data.get("star_rating")
        max_combo = pp_data.get("perfect_combo")
        expected_bpm = pp_data.get("expected_bpm")

        n300 = pp_data.get("n300")
        n100 = pp_data.get("n100") 
        n50 = pp_data.get("n50")
        expected_miss = pp_data.get("misses")

        aim = pp_data.get("aim")
        acc = pp_data.get("acc")
        speed = pp_data.get("speed")

    except Exception as e:
        print(f"neko API failed: {e}")


    user_params["300"]["max"] = n300 
    user_params["300"]["default"] = n300
    user_params["100"]["max"] = n300
    user_params["50"]["max"] = n300
    user_params["мисс"]["max"] = n300

    user_params["300"]["max"] = n300 or 0
    user_params["300"]["default"] = n300 or 0
    user_params["100"]["max"] = n300 or 0
    user_params["50"]["max"] = n300 or 0
    user_params["мисс"]["max"] = n300 or 0
    user_params["cs"]["default"] = values.get("cs", 0)
    user_params["ar"]["default"] = values.get("ar", 0)
    user_params["od"]["default"] = values.get("od", 0)
    user_params["hp"]["default"] = values.get("hp", 0)

    sessions_simulate[user_id] = {
        "username": user_name,
        "status": status,
        "creator": truncate(creator),
        "map_url": map_url,
        "beatmap_escaped": beatmap_escaped,
        "cover_rich_block": cover_rich_block,
        "chat_id": chat_id,
        "message_id": None,
        "topic_id":topic_id,
        "params": {k: v.get("default", "❌ не задано") for k, v in user_params.items()},
        "waiting": None,
        "hint_id": None,
        "schema": user_params,
        "beatmap": map_id,
        "map_combo": max_combo,
        "hit_length": hit_length,
        "hit_length_updated": hit_length,
        "api_mode_accuracy": True, 
        "300_changed": False,
        "100_changed": False,
        "50_changed": False,
        "miss_changed": False,
        "max_hits": n300,
        "grade": str(calculate_rank(n300, n100, n50, expected_miss, True)),
        "aim":aim,
        "acc":acc,
        "speed":speed,
        "acc_u": acc_u,
        "aim_u": aim_u,
        "speed_u": speed_u
    }

    bot_msg = await rich_reply(
        update, 
        markdown=format_text(user_id, pp, max_pp, stars, max_combo, expected_bpm, n300, n100, n50, expected_miss), 
        reply_markup=get_simulate_keyboard(user_id),
        message_thread_id=update.message.message_thread_id
    )
    
    sessions_simulate[user_id]["message_id"] = bot_msg["result"]["message_id"]

    if bot_msg:
        set_message_context(
            bot_msg, 
            reply=False, 
            map_id=int(map_id),
            map_title=full_title,
            mapper_username=creator, 
            origin_call_user_id=update.effective_user.id,
        )

async def skills(user_id: str):

    try:
        user_id = str(user_id)
        saved_name = await check_osu_verified(user_id)
        osu_id = await get_osu_id(user_id)
        best_pp = await get_top_100_scores(saved_name, user_id=osu_id, limit=30, plain=True)
                    
        return await get_skills_by_scores_v2(best_pp)
    
    except:
        return 0, 0, 0
    