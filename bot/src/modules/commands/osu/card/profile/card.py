


import os
import asyncio

from telegram import Update, InputFile
from telegram.ext import ContextTypes

from models.score import Score 
from .....actions.messages import safe_send_message
from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .....systems.auth import check_osu_verified
from .....external.osu_api import get_osu_token, get_user_profile 
from .....external.osu_api import get_best_pp_by_username
from .processing_v1 import create_profile_image
from .utils import delayed_remove
import temp

from config import COOLDOWN_CARD_COMMAND, USER_SETTINGS_FILE
from config import message_authors



async def start_card(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(card(update, context, user_request))

#нужна массивная чистка
async def card(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    query = update.callback_query
    if query:  
        await query.answer()
        message = query.message
    else:
        message = update.message

    can_run = await check_user_cooldown(
            command_name="card",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_CARD_COMMAND,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_CARD_COMMAND} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3 

    user_id = str(update.effective_user.id)
    saved_name = await check_osu_verified(str(update.effective_user.id))

    if update.message:
        temp_message = await update.message.reply_text(
            "`Загрузка...`",
            parse_mode="Markdown"
        )
    elif query:
        if query.message.text or query.message.caption:
            temp_message = await query.message.edit_text(
                "`Загрузка...`",
                parse_mode="Markdown"
            )
        else:
            temp_message = await query.message.reply_text(
                "`Загрузка...`",
                parse_mode="Markdown"
            )

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/c Fujiya` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    message_authors[temp_message.message_id] = update.effective_user.id
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            
            s = temp.load_json(USER_SETTINGS_FILE, default={})
            user_settings = s.get(str(user_id), {}) 
            new_card = user_settings.get("new_card", True)
            user_data["lang"] = user_settings.get("lang", "ru")    

            
            try:
                best_pp = await asyncio.wait_for(get_best_pp_by_username(username, token=token), timeout=10)
            except Exception as e:
                best_pp = "N/A"
                print(e)

            img_path = await asyncio.wait_for(create_profile_image(user_data, best_pp), timeout=15)
            if not img_path:
                print('err in card "not img_path"')
                return
            
            with open(img_path, "rb") as f:
                try:
                    await message.reply_photo(
                        InputFile(f),
                    )
                except:
                    await message.reply_photo(
                        InputFile(f),
                        )
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            except:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)

            asyncio.create_task(delayed_remove(img_path))
            return         
            
        except Exception as e:
            print(f"Ошибка при card (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
