


from telegram import InlineKeyboardMarkup, InlineKeyboardButton



def get_keyboard(page, total_pages, user_id):
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"page_{page-1}_{user_id}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton("След. страница ➡️", callback_data=f"page_{page+1}_{user_id}"))
    return InlineKeyboardMarkup([buttons]) if buttons else None
