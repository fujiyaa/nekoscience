


import os
import json
import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....systems.auth import check_osu_verified
from .buttons_level1 import get_keyboard

from config import COOLDOWN_FARM_COMMAND, USERS_SKILLS_FILE



async def start_farm(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(farm(update, context, user_request))
async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    query = update.callback_query
    if query:  
        await query.answer()
        message = query.message
    else:
        message = update.message

    can_run = await check_user_cooldown(
            command_name="farm",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_FARM_COMMAND,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_FARM_COMMAND} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3

    saved_name = await check_osu_verified(str(update.effective_user.id))

    if update.message:
        temp_message = await update.message.reply_text(
            "`Загрузка...`",
            parse_mode="Markdown"
        )

    if not context.args:
        if saved_name:
            username = saved_name
        else:       
            await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Для использования этой команды должно быть сохранено имя /name`" ,
                    parse_mode="Markdown"
                )
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:  
            try: 
                if os.path.exists(USERS_SKILLS_FILE):
                    with open(USERS_SKILLS_FILE, "r", encoding="utf-8") as f:
                        users_skills = json.load(f)
                else:    
                    users_skills = {}
                
                if username in users_skills:
                    skills = users_skills[username].get("values", {})
                else:
                    raise ValueError(f"Пользователь {username} не найден в JSON")        
            except Exception as e:
                print(e)
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Нет данных о карточке пользователя... Может быть стоит создать новую командой /card, а после этого вернуться сюда?`",
                    parse_mode="Markdown"
                )
                return

            context.user_data["farm_user_id"] = update.effective_user.id
            context.user_data["farm_choices"] = {}
            context.user_data["farm_step"] = 0
            context.user_data["farm_topic_id"] = getattr(update.effective_message, "message_thread_id", None)

           
            await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"Версия:",
                    parse_mode="Markdown",
                    reply_markup=get_keyboard(0)
            )

            return
        except Exception as e:
            print(f"Ошибка при farm (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
