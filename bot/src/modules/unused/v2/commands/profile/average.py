


import asyncio
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from .....actions.messages import safe_send_message
from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .....systems.auth import check_osu_verified
from .buttons import get_keyboard
import temp

from config import COOLDOWN_STATS_COMMANDS, USER_SETTINGS_FILE
from .....systems.translations import DEFAULT_COMMAND_TEMPLATE as T
from .keyboard_types import SELECT_TYPE



async def start_average(update, context):
    await log_all_update(update)
    asyncio.create_task(average(update, context))

async def average(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        telegram_username_str = str(update.effective_user.id)

        can_run = await check_user_cooldown(
                command_name =      "average_stats",
                user_id =           telegram_username_str,
                cooldown_seconds =  COOLDOWN_STATS_COMMANDS,           
                update =            update,
                context =           context,
                warn_text =         f"⏳ {COOLDOWN_STATS_COMMANDS}s"
            )
        
        if not can_run:
            return      
        

        s = temp.load_json(USER_SETTINGS_FILE, default={})
        user_settings = s.get(telegram_username_str, {})
        lang = user_settings.get("lang", "ru")
                            

        saved_name = await check_osu_verified(telegram_username_str)

        if not context.args:
            if saved_name:
                username = saved_name
            else:
                await safe_send_message(
                    update = update,
                    text = f"`{T.get('DEFAULT_HELP')[lang]}`",
                    parse_mode="Markdown")
                return
        else:
            username = " ".join(context.args)

        
        reply_markup = await get_keyboard(
            origin_user_id = update.effective_user.id,
            osu_username = username,
            ruleset = 'osu',
            keyboard_type = SELECT_TYPE,
            language = lang
        )

        if reply_markup is None:
            raise ValueError(
                f'reply_markup is None'
            )

        await update.message.reply_text(
            text = f"`{T.get('Select...')[lang]}`", 
            parse_mode = "Markdown",
            reply_markup = reply_markup
        )

    except Exception:
        traceback.print_exc() 

        try:
            await update.message.reply_text(
                text = f"`{T.get('Error...')[lang]}`", 
                parse_mode = "Markdown"
            )

        except Exception:
            traceback.print_exc()
