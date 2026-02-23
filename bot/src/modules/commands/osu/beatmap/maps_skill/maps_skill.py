


import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from .....actions.messages import safe_send_message
from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .....systems.auth import check_osu_verified
from .....external.osu_api import get_user_profile, get_top_100_scores
from .....external.local_skills import get_skills_by_scores
from .buttons_level1 import get_keyboard

from config import COOLDOWN_MS_COMMAND



async def start_maps_skill(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(maps_skill(update, context, user_request))

async def maps_skill(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="maps_skill",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_MS_COMMAND,           
            update=update,
            context=context
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3 

    user_id = str(update.message.from_user.id)
    saved_name = await check_osu_verified(str(update.effective_user.id))

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            if not context.args:
                if saved_name:
                    username = saved_name
                else:
                    text = (
                        "Использование: `/maps_skill fujina123` <- никнейм\n\n\n"
                        "⚙ *Дополнительно*\n\n"
                        "/name – сохранить ник\n"
                    )
                    await safe_send_message(update, text, parse_mode="Markdown")
                    return
            else:
                username = " ".join(context.args)

            temp_message = await update.message.reply_text(
                "`Загрузка...`", 
                parse_mode="Markdown"
            )
            break

        except: 
            pass

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            user_data = await asyncio.wait_for(get_user_profile(username), timeout=10)
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
                best_scores = await asyncio.wait_for(get_top_100_scores(username, None, user_id, limit=30, plain=True), timeout=10)
            except Exception as e:
                best_scores = "N/A"
                print(e)            

            if isinstance(best_scores, list) and best_scores:
                skills = await get_skills_by_scores(best_scores)

                if not skills:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text="`Неизвестная ошибка, попробуй еще раз`",
                        parse_mode="Markdown"
                        )
                    return  
                
                r_skill = skills.get('raw')

                context.user_data["skills"] = r_skill
                context.user_data["ms_username"] = username
                context.user_data["ms_user_id"] = update.effective_user.id
                context.user_data["ms_choices"] = {}
                context.user_data["ms_step"] = 0
                context.user_data["ms_topic_id"] = getattr(update.effective_message, "message_thread_id", None)

                text = (
                    f'<code>maps_skill v2, поиск по нику: {username}</code>\n'
                    f'\n'
                    f"acc: <b>{r_skill['acc']:.2f}</b> (Точность)\n"
                    f"aim: <b>{r_skill['aim']:.2f}</b> (Аим)\n"
                    f"spd: <b>{r_skill['speed']:.2f}</b> (Скорость)\n"
                    f'\n'
                    f'Выбери версию для поиска:'
                )
                await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML",
                        reply_markup=get_keyboard(0)
                )

                return
        except Exception as e:
            print(f"Ошибка при maps_skill (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
