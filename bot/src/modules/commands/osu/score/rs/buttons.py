


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



async def get_keyboard(
    index: int, 
    total: int, 
    message_id: int, 
    extended: bool = False, 
    loading_image_flag = False
):
    
    buttons, row = [], []
    
    row.append(
        InlineKeyboardButton("⬅️", callback_data=f"rs_prev_{message_id}" if index > 0 else "rs_disabled")
    )
    row.append(
        InlineKeyboardButton(f"{index+1}/{total}", callback_data=f"rs_switchExt_{message_id}")
    )
    row.append(
        InlineKeyboardButton("➡️", callback_data=f"rs_next_{message_id}" if index < total - 1 else "rs_disabled")
    )
    
    buttons.append(row)

    if not extended:
        return InlineKeyboardMarkup(buttons)
    
    row_ext = []
    image_emoji = "⏳" if loading_image_flag else "🖼"    
    row_ext.append(
        InlineKeyboardButton("⏮️", callback_data=f"rs_startExt_{message_id}" if index > 0 else "rs_disabled")
    )
    row_ext.append(
        InlineKeyboardButton("⏪", callback_data=f"rs_prevExt_{message_id}" if index > 0 else "rs_disabled")
    )
    row_ext.append(
        InlineKeyboardButton(image_emoji, callback_data=f"rs_scoreExt_{message_id}" if not loading_image_flag else "rs_disabled")
    )
    row_ext.append(
        InlineKeyboardButton("⏩", callback_data=f"rs_nextExt_{message_id}" if index < total - 1 else "rs_disabled")
    )
    row_ext.append(
        InlineKeyboardButton("⏭️", callback_data=f"rs_endExt_{message_id}" if index < total - 1 else "rs_disabled")
    )

    buttons.append(row_ext)

    return InlineKeyboardMarkup(buttons)
