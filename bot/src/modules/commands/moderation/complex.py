


import asyncio
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from ...actions.messages import safe_send_message, delete_messages_with_delay
from ...systems.cooldowns import check_user_cooldown
from .context import context_lookup
from .buttons import get_keyboard
from .filter import get_vote_limit

from config import COOLDOWN_MOD_VOTE
from .message_text import VOTE_HEADER, VOTE_COUNT


    
async def vote(
    update: Update, context: 
    ContextTypes.DEFAULT_TYPE, 
    action: str = 'delete_message'
):      
    try:  
        can_run = await check_user_cooldown(
                command_name=action,
                user_id=str(update.effective_user.id),
                cooldown_seconds=COOLDOWN_MOD_VOTE,           
                update=update,
                context=context
            )
        if not can_run:
            return

        data_of_reply = await context_lookup(update)

        if not data_of_reply:
            bot_msg = await safe_send_message(
                update,
                'Эта команда работает только при ответе на другое сообщение.',
                'HTML', None, True
            )

            ids_to_delete = [
                update.effective_message.message_id,
                bot_msg.message_id
            ]

            asyncio.create_task(
                delete_messages_with_delay(
                    context,
                    update.effective_chat.id,
                    ids_to_delete,
                    delay=10
                )
            )

            return
        
        if action == 'message_info':

            await safe_send_message(
                update,
                f'{data_of_reply}',
                'HTML', None, True
            )

            return
        
        elif action == 'delete_message':

            text = (
                f"{VOTE_HEADER}\n\n"
                f"{VOTE_COUNT} 0 / {get_vote_limit(update)}\n"
            )

            reply_markup = get_keyboard(
                action, 
                update.effective_message.message_id,
                data_of_reply['message_id']
            )

            await safe_send_message(
                update,
                text,
                'HTML', reply_markup, True
            )

            return

    except Exception:
        traceback.print_exc()
        # ошибку в ответ бота?
