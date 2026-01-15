from telegram import Update
from telegram.ext import ContextTypes

from ....utils.text_format import country_code_to_flag
from .format import format_stats, format_caption
from .fetch import get_profiles
from .send import send

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                      caption: str, 
                      prop: str, 
                      prop_pre: str, prop_post: str, 
                      top_n: int = 10,
                      value_formatter=lambda x: x):

    profiles = await get_profiles(update, context)
    stats_batch = []

    for item in profiles:
        stats = format_stats(item)
        stats_batch.append({
            prop: stats.get(prop),
            'name': stats.get('name'),
            'country_code': stats.get('country_code'),
        })

    stats_batch = sorted(
        stats_batch,
        key=lambda x: float(x.get(prop) or 0),
        reverse=True
    )

    # chat_name = update.effective_chat.full_name
    # if update.effective_chat.is_direct_messages:
    #     chat_name = ''

    text = f"Chat Leaderboard: <b>{caption}</b>\n\n"

    for i, item in enumerate(stats_batch[:top_n], start=1):
        value = value_formatter(item.get(prop))
        text += format_caption(
            i,
            country_code_to_flag(item.get('country_code', '')),
            item.get('name', 'unknown'),
            value,
            prop_pre, prop_post
        )
        text += "\n"

    await send(update, stats_batch, text)
