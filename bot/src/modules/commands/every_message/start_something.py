


import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from ...systems.cooldowns import is_on_cooldown, update_cooldown
from ..service.settings.service import neko_settings
from ..osu.score.score.score import score
from ..osu.profile.complex.router import start_profile
from ..osu.card.profile.card import start_card

from config import COOLDOWN_LINKS_IN_CHAT, OSU_USER_REGEX, OSU_SCORE_REGEX



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
    
    _filter = ['/b', '/s']
    for f in _filter:
        if f in text:
            return False

    match = OSU_USER_REGEX.search(text)
    if not match:
        return False
    
    user_id = match.group(1) 
    context.args = [user_id]

    if not neko_settings.get(update.message.from_user.id, "settings_link_profile_to_card"):
        await start_profile(update, context)
    else:
        await start_card(update, context)

    return True

async def osu_link_score_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or update.message.caption
    if not text: 
        return False
    
    _filter = ['/b', '/u', '/topic', '/comments', '/forum', '/shorts']
    for f in _filter:
        if f in text:
            return False

    match = OSU_SCORE_REGEX.search(text)
    if not match:
        return False
    
    user_id = match.group(1) 
    context.args = [user_id]
    asyncio.create_task(score(update, context, False))
    return True