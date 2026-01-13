


import asyncio
import traceback

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ....actions.messages import safe_send_message, try_send, reset_remove_timer
from ....systems.cooldowns import check_user_cooldown
from ....systems.logging import log_all_update
from ....systems.auth import check_osu_verified
from ....external.osu_api import get_osu_token, get_user_scores
from ....external.osu_http import cache_remaining_scores
from ....wrappers.score import send_score
import temp

from config import COOLDOWN_RS_COMMAND, RS_BUTTONS_TIMEOUT, USER_SETTINGS_FILE, user_sessions



# делает команду асихнхронной
async def start_rs(update, context, is_button_press=False):
    await log_all_update(update)
    asyncio.create_task(rs(update, context, is_button_press))

async def rs(update: Update, context: ContextTypes.DEFAULT_TYPE, is_button_press=False):
    user_id = str(update.effective_user.id)
    can_run = await check_user_cooldown(
        command_name="rs",
        user_id=user_id,
        cooldown_seconds=COOLDOWN_RS_COMMAND,
        update=update,
        context=context,
        warn_text=f"⏳ Подождите {COOLDOWN_RS_COMMAND} секунд"
    )
    if not can_run:
        return

    max_attempts = 2
    caching_reached = False
    for _ in range(max_attempts):
        try:
            if not is_button_press:          
                saved_name = await check_osu_verified(str(update.effective_user.id))
                username = context.args[0] if context.args else saved_name
                if not username:
                    await safe_send_message(update, "⚠ Не указан ник", parse_mode="Markdown")
                    return
            else:
                msg = update.callback_query.message
                session_data = user_sessions.get(msg.message_id)
                if not session_data:
                    await update.callback_query.answer("⚠️ Сессия устарела", show_alert=True)
                    return
                username = session_data["username"]
                saved_name = session_data.get("saved_name", "нет")

            if not is_button_press:
                loading_msg = await try_send(update.message.reply_text, "`загрузка...`", parse_mode="Markdown")

                s = temp.load_json(USER_SETTINGS_FILE, default={})
                user_settings = s.get(str(user_id), {}) 
                fails = user_settings.get("display_fails", True)
                _lang = user_settings.get("lang", "ru") 
                
                if fails: fails = 1

                token = await get_osu_token()
                scores = await get_user_scores(username, token, limit=100, fails=fails)
                if not scores:
                    await safe_send_message(update, "❌ Нет последних игр", parse_mode="Markdown")
                    return           

                score = scores[0]
               
                local_session = {
                    "scores": scores,
                    "index": 0,
                    "user_id": user_id,
                    "username": username,
                    "saved_name": saved_name
                }

                msg = await try_send(send_score, update, score, user_id, local_session, message_id=0)
                await loading_msg.delete()

                message_id = msg.message_id
                user_sessions[message_id] = local_session

                if not caching_reached:
                    asyncio.create_task(cache_remaining_scores(str(scores[0]['osu_score']['user_id']), scores))
                    caching_reached = True
            else:
                msg = update.callback_query.message
                session_data = user_sessions.get(msg.message_id)
                scores = session_data["scores"]
                index = session_data["index"]
                score = scores[index]
                message_id = msg.message_id
                await send_score(update, score, session_data["user_id"], session_data, message_id, query=update.callback_query)

            session = user_sessions[message_id]
            index = session["index"]
            total = len(session["scores"])

            buttons = [
                InlineKeyboardButton("⬅️", callback_data=f"rs_prev_{message_id}" if index > 0 else "rs_disabled"),
                InlineKeyboardButton(f"{index+1}/{total}", callback_data="rs_disabled"),
                InlineKeyboardButton("➡️", callback_data=f"rs_next_{message_id}" if index < total - 1 else "rs_disabled")
            ]

            try:
                keyboard = InlineKeyboardMarkup([buttons])
                await try_send(msg.edit_reply_markup, reply_markup=keyboard)
            except:
                print('keyboard not edited (rs)')

            reset_remove_timer(
                context.bot,
                msg.chat.id,
                msg.message_id,
                RS_BUTTONS_TIMEOUT,
                cleanup=lambda: user_sessions.pop(msg.message_id, None)
            )
            return

        except Exception:
            traceback.print_exc()
