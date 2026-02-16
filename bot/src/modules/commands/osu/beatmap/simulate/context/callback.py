


import traceback

from telegram import Update, LinkPreviewOptions
from telegram.ext import ContextTypes

from ......systems.logging import log_all_update
from ..utils import calculate_rank, format_text
from ..buttons import get_simulate_keyboard
from ......external.osu_http import beatmap, get_beatmap_title_from_file, get_beatmap_creator_from_file
from ......external.localapi import get_map_stats_neko_api
from ......actions.messages import safe_edit_query, safe_query_answer
from ......actions.context import set_message_context

from config import PARAMS_TEMPLATE
from config import sessions_simulate



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid_click = query.from_user.id
     
    parts = query.data.split(":")
    # ["simulate_context", "map", "<map_id>", "<origin_user_id>"]
    action = parts[1]
    map_id = int(parts[2])
    origin_uid = int(parts[3])
    
    if uid_click != origin_uid:
            await safe_query_answer(query, text="Не твои кнопки")
            return
        
    await safe_query_answer(query, show_alert=False)
  
    if action == "cancel":
        await safe_edit_query(query, text="`Отменено`", parse_mode="Markdown")
        return

    if action == "map":   
        try:                    
            await safe_edit_query(query, text="`Загрузка...`", parse_mode="Markdown")

            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            topic_id = getattr(update.effective_message, "message_thread_id", None)
                    
            if user_id in sessions_simulate:
                try:
                    await context.bot.delete_message(chat_id=sessions_simulate[user_id]["chat_id"],
                                                    message_id=sessions_simulate[user_id]["message_id"])
                except:
                    pass
                del sessions_simulate[user_id]

            user_params = {k: v.copy() for k, v in PARAMS_TEMPLATE.items()}

            path, values = await beatmap(map_id)
            stats = {
                "n300": None,
                "n100": None,
                "n50": None,
            }

            #neko API 
            payload = {
                "map_path": str(map_id), 
                
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
                "beatmap": map_id,
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

            link_preview = LinkPreviewOptions(
                url=f"https://osu.ppy.sh/b/{map_id}",
                is_disabled=False,
                prefer_small_media=True,
                prefer_large_media=False,
                show_above_text=True
            )

            bot_msg = await safe_edit_query(query, 
                format_text(user_id, pp, max_pp, stars, max_combo, expected_bpm, n300, n100, n50, expected_miss), 
                reply_markup=get_simulate_keyboard(user_id),
                parse_mode="Markdown",
                link_preview_options=link_preview,
            )
            sessions_simulate[user_id]["message_id"] = bot_msg.message_id

            if bot_msg:
                set_message_context(
                    bot_msg, 
                    reply=False, 
                    map_id=int(map_id),
                    map_title=await get_beatmap_title_from_file(map_id),
                    mapper_username=await get_beatmap_creator_from_file(map_id), 
                    origin_call_user_id=update.effective_user.id,
                )


        except Exception:
            traceback.print_exc() 
