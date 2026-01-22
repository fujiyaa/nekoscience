


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def get_keyboard(step):
    if step == 1:
        buttons = [
            [
                InlineKeyboardButton("0.1x", callback_data="ms_skill:1"),
                InlineKeyboardButton("0.2x", callback_data="ms_skill:2"),
                InlineKeyboardButton("0.3x", callback_data="ms_skill:3"),
                InlineKeyboardButton("0.4x", callback_data="ms_skill:4"),
                InlineKeyboardButton("0.5x", callback_data="ms_skill:5"),
            ],
            [
                InlineKeyboardButton("0.6x", callback_data="ms_skill:6"),
                InlineKeyboardButton("0.7x", callback_data="ms_skill:7"),
                InlineKeyboardButton("0.8x", callback_data="ms_skill:8"),
                InlineKeyboardButton("0.9x", callback_data="ms_skill:9"),
                InlineKeyboardButton("1.0x", callback_data="ms_skill:10"),
            ],
            [
                InlineKeyboardButton("1.1x", callback_data="ms_skill:11"),
                InlineKeyboardButton("1.2x", callback_data="ms_skill:12"),
                InlineKeyboardButton("1.3x", callback_data="ms_skill:13"),
                InlineKeyboardButton("1.4x", callback_data="ms_skill:14"),
                InlineKeyboardButton("1.5x", callback_data="ms_skill:15"),
            ],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data="ms_skill:back"),
            ]           
        ]
    elif step == 3:
        buttons = [
            [
                InlineKeyboardButton("NM", callback_data="ms_mod:NM"),
                InlineKeyboardButton("HD", callback_data="ms_mod:HD"),
                InlineKeyboardButton("HR", callback_data="ms_mod:HR"),                
                InlineKeyboardButton("DT", callback_data="ms_mod:DT"),
                
            ],
            [   
                InlineKeyboardButton("HDHR", callback_data="ms_mod:HDHR"),                
                InlineKeyboardButton("HDDT", callback_data="ms_mod:DTHD"),
                InlineKeyboardButton("DTHR", callback_data="ms_mod:DTHR"),
                InlineKeyboardButton("HDDTHR", callback_data="ms_mod:DTHDHR")
            ],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data="ms_mod:back"),
            ]  
        ]
    elif step == 0:
        buttons = [
            [
                InlineKeyboardButton("Клиент Stable", callback_data="ms_lazer:False"),            
                InlineKeyboardButton("Клиент Lazer", callback_data="ms_lazer:True"),
            ],
            # [
            #     InlineKeyboardButton("⬅️ Назад", callback_data="ms_lazer:back"),
            # ]              
        ]
    elif step == 2:
        buttons = [
            [
                InlineKeyboardButton("1.1x", callback_data="ms_tol:1.1"),
                InlineKeyboardButton("1.2x", callback_data="ms_tol:1.2"),
                InlineKeyboardButton("1.3x", callback_data="ms_tol:1.3"),
                InlineKeyboardButton("1.4x", callback_data="ms_tol:1.4"),
                InlineKeyboardButton("1.5x", callback_data="ms_tol:1.5"),
            ],
            [
                InlineKeyboardButton("1.6x", callback_data="ms_tol:1.6"),
                InlineKeyboardButton("1.7x", callback_data="ms_tol:1.7"),
                InlineKeyboardButton("1.8x", callback_data="ms_tol:1.8"),
                InlineKeyboardButton("1.9x", callback_data="ms_tol:1.9"),
                InlineKeyboardButton("2.0x", callback_data="ms_tol:2.0"),
            ],
            [
                InlineKeyboardButton("⬅️ Назад", callback_data="ms_tol:back"),
            ]  
        ]
    else:
        buttons = []
    return InlineKeyboardMarkup(buttons)
