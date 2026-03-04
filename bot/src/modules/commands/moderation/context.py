


from telegram import Update

from ...actions.context import get_message_context_plain



async def context_lookup(update: Update):

    msg = update.effective_message

    is_reply_to_user = False

    try:            
        is_reply = (
            msg.reply_to_message
            and msg.reply_to_message.from_user
            # and not msg.reply_to_message.from_user.is_bot
        )
        if is_reply:
            is_reply_to_user = (
                msg.reply_to_message.message_id != msg.message_thread_id
            )
    except:
        pass    

    if is_reply_to_user:        
        return get_message_context_plain(update, reply=True)
        
    else:
        return False      
