


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def get_keyboard(step):
    if step == 1:
        buttons = [
            [
                InlineKeyboardButton("30%", callback_data="farm_skill:1"),
                InlineKeyboardButton("40%", callback_data="farm_skill:2"),
                InlineKeyboardButton("50%", callback_data="farm_skill:3"),
                InlineKeyboardButton("60%", callback_data="farm_skill:4"),
                InlineKeyboardButton("70%", callback_data="farm_skill:5"),
            ],
            [
                InlineKeyboardButton("80%", callback_data="farm_skill:6"),
                InlineKeyboardButton("90%", callback_data="farm_skill:7"),
                InlineKeyboardButton("100%", callback_data="farm_skill:8"),
                InlineKeyboardButton("110%", callback_data="farm_skill:9"),
                InlineKeyboardButton("120%", callback_data="farm_skill:10"),
            ]            
        ]
    elif step == 3:
        buttons = [
            [
                InlineKeyboardButton("NM", callback_data="farm_mod:NM"),
                InlineKeyboardButton("HD", callback_data="farm_mod:HD"),
                InlineKeyboardButton("HR", callback_data="farm_mod:HR"),                
                InlineKeyboardButton("DT", callback_data="farm_mod:DT"),
                
            ],
            [   
                InlineKeyboardButton("HDHR", callback_data="farm_mod:HDHR"),                
                InlineKeyboardButton("HDDT", callback_data="farm_mod:DTHD"),
                InlineKeyboardButton("DTHR", callback_data="farm_mod:DTHR"),
                InlineKeyboardButton("HDDTHR", callback_data="farm_mod:DTHDHR")
            ]
        ]
    elif step == 0:
        buttons = [
            [
                InlineKeyboardButton("Клиент Stable", callback_data="farm_lazer:False"),            
                InlineKeyboardButton("Клиент Lazer", callback_data="farm_lazer:True"),
            ],
            
        ]
    elif step == 2:
        buttons = [
            [
                InlineKeyboardButton("±10%", callback_data="farm_tol:1.1"),
                InlineKeyboardButton("±20%", callback_data="farm_tol:1.2"),
                InlineKeyboardButton("±30%", callback_data="farm_tol:1.3"),
                InlineKeyboardButton("±40%", callback_data="farm_tol:1.4"),
                InlineKeyboardButton("±50%", callback_data="farm_tol:1.5"),
            ],
            [
                InlineKeyboardButton("±60%", callback_data="farm_tol:1.6"),
                InlineKeyboardButton("±70%", callback_data="farm_tol:1.7"),
                InlineKeyboardButton("±80%", callback_data="farm_tol:1.8"),
                InlineKeyboardButton("±90%", callback_data="farm_tol:1.9"),
                InlineKeyboardButton("±100%", callback_data="farm_tol:2.0"),
            ]
        ]
    else:
        buttons = []
    return InlineKeyboardMarkup(buttons)
