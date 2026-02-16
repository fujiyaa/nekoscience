


from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import sessions_simulate



def get_simulate_keyboard(user_id):
    schema = sessions_simulate[user_id]["schema"]
    keys = list(schema.keys())
    buttons = []

    for i in range(0, len(keys), 4):
        row = []
        for j in range(4):
            if i + j < len(keys):
                row.append(InlineKeyboardButton(keys[i + j], callback_data=f"simulate_{keys[i + j]}"))
        buttons.append(row)

    buttons.append([InlineKeyboardButton("☑️", callback_data="simulate_close")])

    return InlineKeyboardMarkup(buttons)
