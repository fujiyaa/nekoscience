


import asyncio

from telegram import Update, MessageEntity
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown

from config import COOLDOWN_HELP_COMMAND, HELP_TEXTS, help_hint, help_text



async def start_help(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(help(update, context, user_request))

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    try:
        can_run = await check_user_cooldown(
            command_name="help",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_HELP_COMMAND,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_HELP_COMMAND} секунд"
        )
        if not can_run:
            return
                
        args = context.args  
        if args:
            topic = args[0].lower()
            full_text = HELP_TEXTS.get(topic, f"❓ Нет справки для '{topic}'\n\n" + HELP_TEXTS["default"])
            max_attempts = 3
            for _ in range(max_attempts):
                await update.message.reply_text(full_text, parse_mode='HTML')
                return
        else:            
            full_text = help_text + help_hint        
            entities = [
                MessageEntity(
                    type="expandable_blockquote",
                    offset=0,                     
                    length=len(help_text)+15 # extra offset cos idk         
                )
            ]        
            max_attempts = 3
            for _ in range(max_attempts):
                await update.message.reply_text(full_text, entities=entities)
                return
        
    except Exception as e:
        print(f"Ошибка при doubt: {e}")

