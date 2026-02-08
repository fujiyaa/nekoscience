


import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.cooldowns import check_user_cooldown
from ....actions.messages import safe_send_message
from ....external.osu_api import get_osu_token, get_score_by_id
from ....systems.json_files import load_score_file
from ....wrappers.score import send_score

from config import COOLDOWN_RS_COMMAND



# единственное отличие этой команды в override = True



async def score(update: Update, context: ContextTypes.DEFAULT_TYPE, requested_by_user = True):
    user_id = str(update.effective_user.id)

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

        cached_entry =  await get_score_by_id(score_id, token, override = True)

        if not cached_entry:
            await safe_send_message(update, "❌ Не удалось загрузить скор", parse_mode="Markdown")
            return

        await send_score(update, cached_entry, user_id, user_id, user_id, is_recent=False)

    except Exception:
        traceback.print_exc()
        await safe_send_message(update, "❌ Ошибка при получении скора", parse_mode="Markdown")
