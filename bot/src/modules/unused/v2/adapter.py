


import asyncio
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from ......systems.logging import log_all_update
from .commands_v2 import request_service_action


async def start_average(update, context):
    await log_all_update(update)
    asyncio.create_task(average(update, context))

async def average(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:        
        # cooldown_v2 data
        service = str('telegram_bot')
        action  = str('average')
        user_id = int(update.effective_user.id)

        # args
        command_args = str(context.args)
        
        # telegram
        chat_id = update.effective_chat.id
        thread_id = update.effective_message.message_thread_id
        message_id = update.effective_message.message_id
                
        # adapter job finished
        await request_service_action(
            service,
            action,
            user_id,
            command_args,
            chat_id,
            thread_id,
            message_id
        )

    except Exception:
        traceback.print_exc() 
        # add bot response? 
