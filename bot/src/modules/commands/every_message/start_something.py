


import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from ...systems.cooldowns import is_on_cooldown, update_cooldown
from ..osu.score.score import score
from ..osu.profile.profile import start_profile

from ....config import COOLDOWN_LINKS_IN_CHAT, OSU_USER_REGEX, OSU_SCORE_REGEX



async def start_osu_link_handler(update, context):
    try:
        if await is_on_cooldown("start_osu_link_handler", COOLDOWN_LINKS_IN_CHAT):   
            print('start_osu_link_handler on cooldown')
            return
        else:
            flag = False
            flag = await osu_link_profile_handler(update, context)
            flag = await osu_link_score_handler(update, context)
            if flag:
                await update_cooldown("start_osu_link_handler")
    except Exception as e: print(e)

async def osu_link_profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or update.message.caption
    if not text:
        return False

    match = OSU_USER_REGEX.search(text)
    if not match:
        return False
    
    user_id = match.group(1) 
    context.args = [user_id]
    await start_profile(update, context)
    return True

async def osu_link_score_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or update.message.caption
    if not text: 
        return False

    match = OSU_SCORE_REGEX.search(text)
    if not match:
        return False
    
    user_id = match.group(1) 
    context.args = [user_id]
    asyncio.create_task(score(update, context, False))
    return True