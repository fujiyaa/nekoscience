


import html
import random
import time
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ......actions.messages import safe_send_message
from ......systems.cooldowns import check_user_cooldown
from ......systems.auth import check_osu_verified, get_osu_id
from ......external.osu_api import check_osu_challenge_completed

from ......external.localapi import read_file_neko, insert_to_file_neko, remove_from_file_neko

from ..filter import filter_other_topics
from ..buttons import get_keyboard
from ..json_schema import construct_user, construct_beatmapset

from config import COOLDOWN_CHALLENGE_COMMANDS
from ..tiers import calculate_penalty_for_tier, calculate_points_for_tier

MAX_ATTEMPTS = 1
TIME_LIMIT = 12 * 3600

d_file = "file_daily_challenge"



async def finish_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await filter_other_topics(update, context): 
        return
    
    user_id = str(update.effective_user.id)    
    can_run = await check_user_cooldown(
        command_name="challenge_finish",
        user_id=user_id,
        cooldown_seconds=COOLDOWN_CHALLENGE_COMMANDS,
        update=update,
        context=context       
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

            if osu_id in data:                
                user = data[osu_id]   

                v1 = user["v1"]
                active = v1.get("active")
                completed = v1.get("completed") or {}
                skipped = v1.get("skipped") or {}
                osu = user.get("osu")
                points = v1.get("points").get("current_season", 0)

                osu_name, osu_id, tier = osu.get("username"), osu.get("id"), v1.get("current_tier")

                if active:
                    now = time.time()    
                    
                    beatmap_id = active.get("beatmapset_id")
                    goal, given = active.get("goal"), active.get("given")     

                    # прошлый челлендж не завершен и время не вышло
                    if (now - given) < TIME_LIMIT:
                        if await check_osu_challenge_completed(osu_id, beatmap_id, goal):
                            completed[str(beatmap_id)] = now    

                            keys_to_remove = []
                            keys_to_remove.append(osu_id)

                            await remove_from_file_neko(d_file, keys_to_remove)                            
                            
                            time_taken = now - active.get("given", now)
                            add_points = calculate_points_for_tier(tier, time_taken)
                            points += add_points

                            tier = min(tier + 1, 4)

                            v1_new = {
                                "current_tier":             tier,
                                "points": {
                                    "previous_seasons":     int(v1.get("points").get("previous_seasons", 0)),
                                    "current_season":       int(points),
                                },
                                "active":                   None,
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
                            
                            
                            text = (
                                    f"✅ Челлендж {osu_name} завершен! +{add_points} очков (баланс {points})\n\n"
                            )
                            reply_markup = get_keyboard("finish")

                        # время еще есть
                        else:
                            text = (
                                    f"🚫 Челлендж {osu_name} еще не завершен!\n\n"
                            )
                            reply_markup = get_keyboard("finish-still-active")

                    # не завершен но время вышло
                    else:
                        skipped[str(beatmap_id)] = now    

                        keys_to_remove = []
                        keys_to_remove.append(osu_id)

                        await remove_from_file_neko(d_file, keys_to_remove)

                        tier = 1

                        v1_new = {
                            "current_tier":             tier,
                            "points": {
                                "previous_seasons":     int(v1.get("points").get("previous_seasons", 0)),
                                "current_season":       int(v1.get("points").get("current_season", 0))
                            },
                            "active":                   None,
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
                        
                        text = (
                                f"🤔 Этот челлендж {osu_name} пропущен, так как время вышло\n\n"
                        )
                        reply_markup = get_keyboard("finish")
                
                # нет активного 
                else:
                    text = (
                        f"⏭️🚫 У {osu_name} не было активного челленджа\n\n"
                    )
                    reply_markup = get_keyboard("finish")
            else:
                text = (
                    f"⏭️🚫 У {osu_name} не было активного челленджа\n\n"
                )
                reply_markup = get_keyboard("finish")

            await safe_send_message(
                update,
                text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )            

            return
        except Exception:
            traceback.print_exc()
