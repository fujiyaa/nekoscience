


import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ......actions.messages import safe_send_message
from ......systems.cooldowns import check_user_cooldown

from ......external.localapi import read_file_neko

from config import COOLDOWN_CHALLENGE_COMMANDS, ADMINS

MAX_ATTEMPTS = 1

d_file = "file_daily_challenge"



async def challenge_mark_done(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    user_id = str(update.effective_user.id)    
    can_run = await check_user_cooldown(
        command_name="challenge_mark_done",
        user_id=user_id,
        cooldown_seconds=COOLDOWN_CHALLENGE_COMMANDS,
        update=update,
        context=context,
        warn_text=f"⏳ Подождите {COOLDOWN_CHALLENGE_COMMANDS} секунд"        
    )    
    if not can_run or update.effective_user.username is None:
        return
    
    user_id_telegram = update.effective_user.id
    if user_id_telegram not in ADMINS:
        await update.message.reply_text("❌ У тебя нет прав для использования этой команды.")
        return

    if not context.args:
        await update.message.reply_text("❗️ Нужно указать Telegram username. Использование: /markdone <username>")
        return

    username = " ".join(context.args)
    if username.startswith("@"):
        username = username[1:]


    # ваш вайбкод здесь
    
    return  
