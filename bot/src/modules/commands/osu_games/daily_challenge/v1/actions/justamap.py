


import html
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ......actions.messages import safe_send_message
from ......systems.cooldowns import check_user_cooldown
from ......external.osu_api import get_random_beatmap_from_random_pack

from ..filter import filter_other_topics
from ..buttons import get_keyboard

from config import COOLDOWN_CHALLENGE_COMMANDS

MAX_ATTEMPTS = 1



async def justamap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await filter_other_topics(update, context): 
        return
    
    user_id = str(update.effective_user.id)    
    can_run = await check_user_cooldown(
        command_name="challenge_next",
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
            beatmap_info = await get_random_beatmap_from_random_pack()
            if not beatmap_info:
                await context.bot.safe_send_message(update, text="❌ Не удалось получить карту", parse_mode="HTML")
                return            
            
            beatmapset = beatmap_info

            set_id = beatmapset.get("beatmapset_id")                    
            artist,  title  =  html.escape(beatmapset.get("artist")),  html.escape(beatmapset.get("title"))
            creator, bg_url =  html.escape(beatmapset.get("creator")), beatmapset.get("bg_url")
            
            text = (
                    f"🫖 Случайная карта для @{tg_name}:\n\n"
                    f"<b>Карта</b>: <a href=\"https://osu.ppy.sh/beatmapsets/{set_id}\">{title}</a> — {artist} (by {creator})\n\n"
                    f"<b>Цель</b>: без цели\n\n"
            )
            reply_markup = get_keyboard("justamap")

            await safe_send_message(
                update,
                text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

            return
        except Exception:
            traceback.print_exc()
    