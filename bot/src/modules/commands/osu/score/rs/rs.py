


import asyncio
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from .....external.osu_http import get_beatmap_title_from_file, get_beatmap_creator_from_file
from .....actions.messages import safe_send_message, try_send, reset_remove_timer
from .....systems.cooldowns import check_user_cooldown
from .....systems.logging import log_all_update
from .....systems.auth import check_osu_verified
from .....external.osu_api import get_user_scores
from .....wrappers.score import send_score
from .....actions.context import set_message_context
from .buttons import get_keyboard
import temp

from config import COOLDOWN_RS_COMMAND, RS_BUTTONS_TIMEOUT, USER_SETTINGS_FILE, user_sessions
from .....systems.translations import DEFAULT_COMMAND_TEMPLATE as DT


# делает команду асихнхронной
async def start_rs(update, context):
    await log_all_update(update)
    asyncio.create_task(rs(update, context))

async def rs(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    try:
        user_id = str(update.effective_user.id)
        can_run = await check_user_cooldown(
            command_name="rs",
            user_id=user_id,
            cooldown_seconds=COOLDOWN_RS_COMMAND,
            update=update,
            context=context
        )
        if not can_run:
            return

        s = temp.load_json(USER_SETTINGS_FILE, default={})
        user_settings = s.get(str(user_id), {}) 
        fails = user_settings.get("display_fails", True)
        l = user_settings.get("lang", "ru")

        saved_name = await check_osu_verified(str(update.effective_user.id))
        username = context.args[0] if context.args else saved_name            
        if fails: fails = 1

        if not username:
            await safe_send_message(
                update, 
                f"`{DT.get('No nickname saved...')[l]}`", 
                parse_mode="Markdown"
            )
            return

        loading_msg = await try_send(
            update.message.reply_text, 
                f"`{DT.get('Loading...')[l]}`", 
                parse_mode="Markdown"
            )

        scores = await get_user_scores(username, limit=100, fails=fails)
        if not scores:
            await safe_send_message(
                update, 
                f"`{DT.get('No recent scores...')[l]}`", 
                parse_mode="Markdown"
            )
            return           

        score = scores[0]
        
        local_session = {
            "scores": scores,
            "index": 0,
            "user_id": user_id,
            "username": username,
            "saved_name": saved_name,
            "keyboardExt": False
        }

        msg = await try_send(send_score, update, score, user_id, local_session, message_id=0)
        
        map_id=score.get('map').get('beatmap_id')
        if msg:
            set_message_context(
                msg, 
                reply=False, 
                map_id=map_id, 
                map_title=await get_beatmap_title_from_file(map_id),
                mapper_username=await get_beatmap_creator_from_file(map_id),
                origin_call_user_id=update.effective_user.id,
            )

        await loading_msg.delete()

        message_id = msg.message_id
        user_sessions[message_id] = local_session        
        session = user_sessions[message_id]

        reply_markup = await get_keyboard(session["index"], len(session["scores"]), message_id)
        
        msg = await try_send(
            msg.edit_reply_markup, 
            reply_markup=reply_markup
        )

        reset_remove_timer(
            context.bot,
            msg.chat.id,
            msg.message_id,
            RS_BUTTONS_TIMEOUT,
            cleanup=lambda: user_sessions.pop(msg.message_id, None)
        )

    except Exception:
        traceback.print_exc()
