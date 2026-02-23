


import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ......actions.messages import safe_send_message
from ......systems.cooldowns import check_user_cooldown
from ..filter import filter_other_topics

from ..buttons import get_keyboard

from config import COOLDOWN_CHALLENGE_COMMANDS

MAX_ATTEMPTS = 1

d_file = "file_daily_challenge"



async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    user_id = str(update.effective_user.id)    
    can_run = await check_user_cooldown(
        command_name="challenge_leaderboard",
        user_id=user_id,
        cooldown_seconds=COOLDOWN_CHALLENGE_COMMANDS,
        update=update,
        context=context       
    )    
    if not can_run or update.effective_user.username is None:
        return    
    
    for _ in range(MAX_ATTEMPTS):
        try:
            text = (
                "<b>Как работают челленджи (бета):</b>\n\n"
                "Играть можно <b>любую сложность мапсета</b> с любыми ранкед модами\n\n"
                "Челленджи делятся на уровни — <b>Tier 1</b> -> <b>T2</b> - <b>T3</b> - <b>T4</b>\n\n"
                "T1 стоит <b>больше очков</b> чем T2, T2 больше чем T3 и т.д...\n\n"
                "Каждый новый челлендж повышает Tier на <b>1</b> \n\n"
                "Через 12 часов после последнего запроса челленджа Tier <b>сбрасывается</b> до 1\n\n"        
                "Челлендж можно пропустить, но на это потратятся очки\n\n"
                "Если после получения челленджа пройдет 12 часов, он просто исчезнет, очки не потеряются\n\n"
            )

            if not await filter_other_topics(update, context): 
                reply_markup = None
            else:
                reply_markup = get_keyboard("leaderboard")            

            await safe_send_message(
                update,
                text,
                parse_mode="HTML",
                reply_markup=reply_markup
            )            

            return
        except Exception:
            traceback.print_exc()
    