


from telegram import Update
from telegram.ext import ContextTypes

from ....actions.messages import safe_query_answer

from config import sessions_simulate



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    sess = sessions_simulate.get(user_id)

    if not sess or sess["message_id"] != query.message.message_id:
        return await safe_query_answer(query, "❌ Это меню не для вас")

    if query.data == "simulate_close":
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=sess["chat_id"],
                message_id=sess["message_id"],
                reply_markup=None
            )
        except:
            pass

        if sess.get("hint_id"):
            try:
                await context.bot.delete_message(chat_id=sess["chat_id"], message_id=sess["hint_id"])
            except:
                pass

        del sessions_simulate[user_id]
        return await safe_query_answer(query, "✅ Меню закрыто")

    schema = sess["schema"]
    param_name = query.data.replace("simulate_", "", 1)
    if param_name not in schema:
        return await safe_query_answer(query, "❌ Неизвестный параметр")

    await safe_query_answer(query, text=None, show_alert=False)
    sess["waiting"] = param_name

    if sess.get("hint_id"):
        try:
            await context.bot.delete_message(chat_id=sess["chat_id"], message_id=sess["hint_id"])
        except:
            pass

    hint_msg = await context.bot.send_message(
        sess["chat_id"],
        message_thread_id=sess["topic_id"],
        text=f"👉 @{query.from_user.username or query.from_user.first_name}, {schema[param_name]['msg']}"
    )
    sess["hint_id"] = hint_msg.message_id
