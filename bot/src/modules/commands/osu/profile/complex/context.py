


from telegram import Update
from telegram.ext import ContextTypes

from .....systems.auth import check_osu_verified
from .....actions.messages import safe_send_message
from .....actions.context import get_message_context
from .buttons import get_keyboard



async def context_lookup(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    action: str = 'profile'
):
    
    saved_name = await check_osu_verified(str(update.effective_user.id))

    if not context.args:   

        # check verified by reply
        msg = update.effective_message

        is_reply_to_user = False

        try:            
            is_reply = (
                msg.reply_to_message
                and msg.reply_to_message.from_user
                and not msg.reply_to_message.from_user.is_bot
            )
            if is_reply:
                is_reply_to_user = (
                    msg.reply_to_message.message_id != msg.message_thread_id
                )
        except:
            pass

        if is_reply_to_user:
            username = await check_osu_verified(str(msg.reply_to_message.from_user.id))

            if not username:
                await safe_send_message(
                    update, 
                    text=f"{msg.reply_to_message.from_user.first_name} не авторизован, нельзя посмотреть осу профиль...",                     
                )
                return None, None
        
        else:
            message_context = get_message_context(update, reply=False)          
            message_context_reply = get_message_context(update, reply=True)      
            if message_context:
                extra_name1 = extra_name2 = None
                extra_name1 = await check_osu_verified(message_context["metadata"].get("origin_call_user_id"))
                if message_context_reply:
                    extra_name2 = await check_osu_verified(message_context_reply["metadata"].get("origin_call_user_id"))

                if message_context["metadata"].get("profile_player_username") is not None or (
                    message_context["metadata"].get("mapper_username") is not None) or (
                    extra_name1 is not None) or (extra_name2 is not None
                    ):   
                    
                    username = None
                    if saved_name:
                        username = saved_name  
                        
                    temp_message = await safe_send_message(
                        update, 
                        text=f"<code>Посмотреть {action}...\n(или используй /profile +ник)</code>", 
                        reply_markup=await get_keyboard(
                            message_context,
                            message_context_reply,
                            username,                        
                            update.effective_user.id,
                            action
                        ),
                        parse_mode="HTML"
                    )

                    return None, None
            
            if saved_name:
                username = saved_name       

            else:
                text = (
                    "`помощь: /help`"
                )
                temp_message = await safe_send_message(update, text, parse_mode="Markdown")

                return None, None
    else:
        username = " ".join(context.args)

    
    if action == 'average':
        return update.effective_message, username
    

    if update.message:
        temp_message = await update.message.reply_text(
            "`Загрузка...`",
            parse_mode="Markdown"
        )

    return temp_message, username
