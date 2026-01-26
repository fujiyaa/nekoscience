


import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown
from ....systems.auth import check_osu_verified
from ....actions.messages import safe_send_message
from ....external.osu_api import get_osu_token, get_user_profile, get_top_100_scores
from ....actions.context import set_message_context, get_message_context
from ....wrappers.osu_profile import get_profile_text
from .buttons import get_keyboard

from config import COOLDOWN_STATS_COMMANDS



async def start_profile(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(profile(update, context, user_request))
    
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):  
    can_run = await check_user_cooldown(
            command_name="profile",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return

    
    user_id = str(update.effective_user.id)
    saved_name = await check_osu_verified(str(update.effective_user.id))

    if not context.args:   

        # check verified by reply
        msg = update.effective_message

        is_reply_to_user = (
            msg.reply_to_message
            and msg.reply_to_message.from_user
            and not msg.reply_to_message.from_user.is_bot
        )

        if is_reply_to_user:
            username = await check_osu_verified(str(msg.reply_to_message.from_user.id))

            if not username:
                await safe_send_message(
                    update, 
                    text=f"{msg.reply_to_message.from_user.first_name} не авторизован, нельзя посмотреть осу профиль...",                     
                )
                return
        
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
                    
                    if saved_name:
                        username = saved_name  
                        
                    await safe_send_message(
                        update, 
                        text=f"<code>Посмотреть профиль...\n(или используй /profile +ник)</code>", 
                        reply_markup=await get_keyboard(
                            message_context,
                            message_context_reply,
                            username,                        
                            update.effective_user.id,
                        ),
                        parse_mode="HTML"
                    )
                    return
            
            if saved_name:
                username = saved_name       
            else:
                text = (
                    "Использование: `/p Fujiya` <- никнейм"
                    "⚙ *Дополнительно*\n\n"
                    "/name – сохранить ник\n"
                )
                await safe_send_message(update, text, parse_mode="Markdown")
                return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    if update.message:
        temp_message = await update.message.reply_text(
            "`Загрузка...`",
            parse_mode="Markdown"
        )
    
    MAX_ATTEMPTS = 3
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Игрок не найден`",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_pp = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_pp = []
                print(e)

            text = get_profile_text(user_data, best_pp)

            if text is None:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Нет данных`",
                    parse_mode="Markdown"
                )
                return
            
        
            bot_msg = await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=temp_message.message_id,
                text=text,
                parse_mode="HTML"
            )

            if bot_msg:
                set_message_context(
                    bot_msg, 
                    reply=False,
                    profile_player_username=username,
                    origin_call_user_id=update.effective_user.id,
                )

            return
                        

        except Exception as e:
            print(f"Ошибка при profile (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )