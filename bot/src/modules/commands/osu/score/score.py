


import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.cooldowns import check_user_cooldown
from ....actions.messages import safe_send_message
from ....external.osu_api import get_osu_token, get_score_by_id
from ....wrappers.score import send_score
from ....actions.context import set_cached_map

from config import COOLDOWN_RS_COMMAND     # why



# не асинхронная потому что вызывается только из асинхронной обертки start_osu_link_handler
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE, requested_by_user = True):
    user_id = str(update.effective_user.id)
    print('async def score')

    if requested_by_user:
        can_run = await check_user_cooldown(
            command_name="score",
            user_id=user_id,
            cooldown_seconds=COOLDOWN_RS_COMMAND,
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_RS_COMMAND} секунд"
        )
        if not can_run:
            return

    if context.args:
        score_id = context.args[0]
    else:
        await safe_send_message(update, "⚠ Не указан ID скора", parse_mode="Markdown")
        return

    try:
        token = await get_osu_token()

        cached_entry =  await get_score_by_id(score_id, token)

        if not cached_entry:
            await safe_send_message(update, "❌ Не удалось загрузить скор", parse_mode="Markdown")
            return

        bot_msg = await send_score(update, cached_entry, user_id, user_id, user_id, is_recent=False)
       
        if bot_msg:
            bot_msg_id = bot_msg.message_id
            user_to_cache = update.effective_user.id
            map_to_cache = cached_entry.get('map').get('beatmap_id')
            
            set_cached_map(bot_msg, map_to_cache, user_to_cache, bot_msg_id)
            
    except Exception:
        traceback.print_exc()
        await safe_send_message(update, "❌ Ошибка", parse_mode="Markdown")

    
