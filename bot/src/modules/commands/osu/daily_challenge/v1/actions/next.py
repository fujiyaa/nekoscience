


import html
import random
import time
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ......actions.messages import safe_send_message
from ......systems.cooldowns import check_user_cooldown
from ......systems.auth import check_osu_verified, get_osu_id
from ......external.osu_api import get_random_beatmap_from_random_pack

from ......external.localapi import read_file_neko, insert_to_file_neko, remove_from_file_neko

from ..filter import filter_other_topics
from ..buttons import get_keyboard
from ..json_schema import construct_user, construct_beatmapset

from config import COOLDOWN_CHALLENGE_COMMANDS
from ..goals import goals

MAX_ATTEMPTS = 1
TIME_LIMIT = 12 * 3600

d_file = "file_daily_challenge"



async def next_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await filter_other_topics(update, context): 
        return
    
    user_id = str(update.effective_user.id)    
    can_run = await check_user_cooldown(
        command_name="challenge_next",
        user_id=user_id,
        cooldown_seconds=COOLDOWN_CHALLENGE_COMMANDS,
        update=update,
        context=context,
        warn_text=f"⏳ Подождите {COOLDOWN_CHALLENGE_COMMANDS} секунд"        
    )    
    if not can_run or update.effective_user.username is None:
        return    
    else:    
        tg_id = update.effective_user.id 
        tg_name = update.effective_user.username

    for _ in range(MAX_ATTEMPTS):
        try:                   
            osu_name = await check_osu_verified(user_id)
            if not osu_name:
                await safe_send_message(
                    update, "⚠ Не сохранен ник, это делается командой /name", 
                    parse_mode="Markdown")
                return            
            
            osu_id = await get_osu_id(user_id)
            if osu_id: 
                osu_id = str(osu_id) 
            else: 
                return    
            
            response = await read_file_neko(d_file)
            data = response.get("current", {})

            if osu_id not in data:
                data[osu_id] = construct_user(
                    osu_id, 
                    osu_name, 
                    tg_id,
                    tg_name
                )
                await insert_to_file_neko(d_file, data)

            user = data[osu_id]   

            v1 = user["v1"]
            active = v1.get("active")
            completed = v1.get("completed") or {}
            skipped = v1.get("skipped") or {}
            osu = user.get("osu")

            osu_name, osu_id, tier = osu.get("username"), osu.get("id"), v1.get("current_tier")

            is_new_challenge_needed = False

            if active:
                now = time.time()

                beatmap_id = active.get("beatmapset_id")
                goal, given = active.get("goal"), active.get("given")     

                # прошлый челлендж не завершен и время не вышло
                if (now - given) < TIME_LIMIT:
                    set_id = active.get("beatmapset_id")                    
                    artist,  title  = html.escape(active.get("artist")),  html.escape(active.get("title"))
                    creator, bg_url =  html.escape(active.get("creator")), active.get("bg_url")

                    text = (
                        f"🎯 Текущий челлендж для {osu_name} (Tier {tier}):\n\n"
                        f"<b>Карта</b>: <a href=\"https://osu.ppy.sh/beatmapsets/{set_id}\">{title}</a> — {artist} (by {creator})\n\n"
                        f"<b>Цель</b>: {html.escape(goal)}\n\n"
                    )
                    reply_markup = get_keyboard("next")

                # если время вышло
                else:
                    tier = 1
                    skipped[str(beatmap_id)] = now  
                    is_new_challenge_needed = True
            
            # нет активного 
            else:   is_new_challenge_needed = True

            if is_new_challenge_needed:     
                beatmap_info = await get_random_beatmap_from_random_pack()
                if not beatmap_info:
                    await context.bot.safe_send_message(update, text="❌ Не удалось получить карту", parse_mode="HTML")
                    return
                
                now = time.time()

                completed_times = list(completed.values()) or []
                skipped_times = list(skipped.values()) or []

                if not completed_times and not skipped_times:
                    tier = 1
                else:
                    t_last = max(completed_times + skipped_times)
                    delta = now - t_last

                    if delta > TIME_LIMIT:
                        tier = 1

                
                goal = html.escape(random.choice(goals))

                beatmapset = construct_beatmapset(beatmap_info, goal)

                keys_to_remove = []
                keys_to_remove.append(osu_id)

                await remove_from_file_neko(d_file, keys_to_remove)

                v1_new = {
                    "current_tier":             tier,
                    "points": {
                        "previous_seasons":     int(v1.get("points").get("previous_seasons", 0)),
                        "current_season":       int(v1.get("points").get("current_season", 0))
                    },
                    "active":                   beatmapset,
                    "skipped":                  skipped,
                    "completed":                completed
                }

                data[osu_id] = construct_user(
                    osu_id, 
                    osu_name, 
                    tg_id,
                    tg_name,
                    v1 = v1_new
                )

                await insert_to_file_neko(d_file, data)
                
                set_id = beatmapset.get("beatmapset_id")                    
                artist,  title  =  html.escape(beatmapset.get("artist")),  html.escape(beatmapset.get("title"))
                creator, bg_url =  html.escape(beatmapset.get("creator")), beatmapset.get("bg_url")
                
                text = (
                        f"🎯 Текущий челлендж для {osu_name} (Tier {tier}):\n\n"
                        f"<b>Карта</b>: <a href=\"https://osu.ppy.sh/beatmapsets/{set_id}\">{title}</a> — {artist} (by {creator})\n\n"
                        f"<b>Цель</b>: {html.escape(goal)}\n\n"
                )
                reply_markup = get_keyboard("next")

            await safe_send_message(
                update,
                text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

            return
        except Exception:
            traceback.print_exc()
    