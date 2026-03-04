


from telegram import Update
from telegram.ext import ContextTypes

from ...actions.messages import delete_messages_with_delay_in_que
from .vote_cache import register_vote, get_vote_counts
from .filter import get_vote_limit

from .vote_cache import VOTE_CACHE
from .message_text import VOTE_HEADER, VOTE_COUNT, VOTE_POS, VOTE_NEG



async def vote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # modv:dmsg:positive:12345
    _, _, vote_type, origin_id, request_id = query.data.split(":")
    origin_id = int(origin_id)

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    success = register_vote(origin_id, user_id, vote_type)

    if not success:
        await query.answer("Вы уже голосовали так же.", show_alert=True)
        return

    positive, negative = get_vote_counts(origin_id)

    vote_limit = get_vote_limit(update)

    if (positive - negative) >= vote_limit:
        try:

            new_text = (
                f"{VOTE_POS}\n\n"
                f"{VOTE_COUNT} {positive - negative} / {vote_limit}\n"
            )
            
            await query.message.edit_text(
                new_text,
                reply_markup=query.message.reply_markup,
                parse_mode="HTML"
            )

            await delete_messages_with_delay_in_que(
                context,
                chat_id,
                [request_id, origin_id, query.message.message_id],
                delay=5,
                que_delay=0
            )

            VOTE_CACHE.pop(origin_id, None)

        except Exception as e:
            print(f"Ошибка удаления: {e}")

        return 

    if (negative - positive) >= vote_limit:
        try:
            new_text = (
                f"{VOTE_NEG}\n\n"
                f"{VOTE_COUNT} {positive - negative} / {vote_limit}\n"
            )
            
            await query.message.edit_text(
                new_text,
                reply_markup=query.message.reply_markup,
                parse_mode="HTML"
            )  

            await delete_messages_with_delay_in_que(
                context,
                chat_id,
                [origin_id, query.message.message_id],
                delay=10,
                que_delay=0
            )

            VOTE_CACHE.pop(origin_id, None)

        except Exception as e:
            print(f"Ошибка удаления: {e}")

        return   
    

    new_text = (
        f"{VOTE_HEADER}\n\n"
        f"{VOTE_COUNT} {positive - negative} / {vote_limit}\n"
    )

    await query.message.edit_text(
        new_text,
        reply_markup=query.message.reply_markup,
        parse_mode="HTML"
    )