


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def get_keyboard(page, total_pages, user_id):
    
    btn_back = InlineKeyboardButton("⬅️ Назад", callback_data=f"ms_page:{user_id}:{page-1}")
    btn_next = InlineKeyboardButton("Вперед ➡️", callback_data=f"ms_page:{user_id}:{page+1}")
    btn_mods = InlineKeyboardButton("🔄 Изменить", callback_data=f"ms_lazer:select_mods_again")
    btn_main = InlineKeyboardButton("♻️ Выбрать все заново", callback_data=f"ms_skill:back")

    if page == 0:
        if total_pages == 1:
            buttons = [
                [btn_mods],
                [btn_main]
            ]
        else:
            buttons = [
                [btn_mods, btn_next],
                [btn_main]
            ]
    elif page == (total_pages - 1):
        buttons = [
            [btn_back, btn_mods],
            [btn_main]
        ]
    else:
        buttons = [
            [btn_back, btn_mods, btn_next],
            [btn_main]
        ]      
    
    return InlineKeyboardMarkup(buttons)
