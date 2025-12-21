


import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from .utils import calculate_rank, format_text
from .buttons import get_simulate_keyboard
from ....external.osu_http import beatmap
from ....external.localapi import get_map_stats_neko_api
from ....actions.messages import delete_user_message, delete_message_after_delay

from .....config import OSU_MAP_REGEX, PARAMS_TEMPLATE
from .....config import sessions_simulate



async def simulate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    topic_id = getattr(update.effective_message, "message_thread_id", None)

    message_text = update.message.text.strip()
    match = OSU_MAP_REGEX.search(message_text)

    if not match:        
        msg = await update.message.reply_text(
            "❌ Нужна ссылка на карту"
        )
        asyncio.create_task(delete_message_after_delay(context, msg.chat.id, msg.message_id, 5))
        asyncio.create_task(delete_user_message(update, context, delay=4))
        return

    beatmap_id = match.group(1) if match.group(1) else match.group(2)

    if user_id in sessions_simulate:
        try:
            await context.bot.delete_message(chat_id=sessions_simulate[user_id]["chat_id"],
                                             message_id=sessions_simulate[user_id]["message_id"])
        except:
            pass
        del sessions_simulate[user_id]

    user_params = {k: v.copy() for k, v in PARAMS_TEMPLATE.items()}

    path, values = await beatmap(beatmap_id)
    stats = {
        "n300": None,
        "n100": None,
        "n50": None,
    }

    #neko API 
    payload = {
        "map_path": str(beatmap_id), 
        
        "n300": 0,
        "n100": 0,
        "n50": 0,
        "misses": 0,                   
        
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

    sessions_simulate[user_id] = {
        "chat_id": chat_id,
        "message_id": None,
        "topic_id":topic_id,
        "params": {k: v.get("default", "❌ не задано") for k, v in user_params.items()},
        "waiting": None,
        "hint_id": None,
        "schema": user_params,
        "path": path,
        "beatmap": beatmap_id,
        "values": values,
        "map_combo": max_combo,
        "300_changed": False,
        "100_changed": False,
        "50_changed": False,
        "miss_changed": False,
        "max_hits": n300,
        "grade": str(calculate_rank(n300, n100, n50, expected_miss, True)),
        "aim":aim,
        "acc":acc,
        "speed":speed,
    }

    msg = await update.message.reply_text(format_text(user_id, pp, max_pp, stars, max_combo, expected_bpm, n300, n100, n50, expected_miss), 
                                          reply_markup=get_simulate_keyboard(user_id),
                                          parse_mode="Markdown" )
    sessions_simulate[user_id]["message_id"] = msg.message_id

