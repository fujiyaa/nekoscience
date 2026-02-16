


import time
import asyncio
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from .....actions.messages import safe_send_message
from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .....systems.auth import check_osu_verified, get_osu_id

from .....external.localapi import read_file_neko, insert_to_file_neko

from .filter import filter_other_topics
from .buttons import get_keyboard
from .json_schema import construct_user

from config import COOLDOWN_CHALLENGE_COMMANDS

MAX_ATTEMPTS = 3
TIME_LIMIT = 12 * 3600

d_file = "file_daily_challenge"



async def start_challenge(update, context):
    await log_all_update(update)
    asyncio.create_task(challenge(update, context))

async def challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await filter_other_topics(update, context): 
        return

    user_id = str(update.effective_user.id)
    can_run = await check_user_cooldown(
        command_name="challenge_main",
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
                    tg_name,
                )
                await insert_to_file_neko(d_file, data)

            user = data[osu_id]            
            v1 = user["v1"]
            active = v1.get("active")            

            if not active:
                text = "📑 Главное меню дейли"
                reply_markup = get_keyboard("main")
            else:
                now = time.time()

                tier = v1.get("current_tier")                
                given = active.get("given")     

                # прошлый челлендж не завершен и время не вышло
                if (now - given) < TIME_LIMIT:                    
                    remaining_seconds = max(TIME_LIMIT - (now - given), 0)
                    reset = int(remaining_seconds // 60)

                    if tier != 1:
                        text = (
                            f"🎯❗ <b>Есть не выполненный челлендж</b>\n\n"
                            f"Не пройден челлендж с <b>Tier {tier}</b>\n"
                            f"Сброс до Tier 1 через <b>{reset} мин</b>"
                        )
                    else:
                        text = (
                            f"🎯❗ <b>Есть не выполненный челлендж</b>\n\n"
                            f"Не пройден челлендж с <b>Tier {tier}</b>"
                        )
                    reply_markup = get_keyboard("main-active")
                    
                else:
                    text = "📑 Главное меню дейли"
                    reply_markup = get_keyboard("main")                
            
            await safe_send_message(
                update,
                text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )            

            return
        except Exception:
            traceback.print_exc()
