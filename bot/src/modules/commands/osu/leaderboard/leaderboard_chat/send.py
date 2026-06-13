


from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from .....actions.rich import edit_rich_query



async def send(query: CallbackQuery, stats_batch: dict = None, caption: str = ''):
    if not stats_batch:
                
        keyboard = [
            [
                InlineKeyboardButton("⬅️ Назад",
                callback_data=f"leaderboard_chat_back:{query.from_user.id}")
            ]
        ]

        reply_markup=InlineKeyboardMarkup(keyboard)        
        text = "### <code>Нет данных</code>"

        await edit_rich_query(
            query,
            markdown=text,
            reply_markup=reply_markup
        )

        return
           
    keyboard = [
        [
            InlineKeyboardButton("⬅️ Назад",
            callback_data=f"leaderboard_chat_back:{query.from_user.id}")
        ]
    ]

    reply_markup=InlineKeyboardMarkup(keyboard)

    await edit_rich_query(
        query,
        markdown=caption,
        reply_markup=reply_markup
    )
