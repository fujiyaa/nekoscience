


from telegram import Update
from telegram.ext import ContextTypes

from .actions.finish import finish_challenge
from .actions.info import info
from .actions.leaderboard import leaderboard
from .actions.next import next_challenge
from .actions.skip import skip_challenge
from .challenge import challenge



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    await query.answer()

    try:
        if data   == "challenge_next":
            await               next_challenge(     update, context)
        elif data == "challenge_finish":
            await               finish_challenge(   update, context)
        elif data == "challenge_leaderboard":
            await               leaderboard(        update, context)
        elif data == "challenge_info":
            await               info(               update, context)
        elif data == "challenge_skip":
            await               skip_challenge(     update, context)
        elif data == "challenge_main":
            await               challenge(          update, context)
        else:
            await query.edit_message_text("Неизвестная кнопка!")
    except Exception as e: print (e)
