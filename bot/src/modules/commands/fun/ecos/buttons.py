


from telegram import InlineKeyboardButton, InlineKeyboardMarkup



def get_main_keyboard(owner_id):

    return InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "〰️ Играть 〰️",
            callback_data=f"eco_actions:{owner_id}"
        )
    ],
    [
        InlineKeyboardButton(
            "🎒 Инвентарь",
            callback_data=f"eco_inventory:{owner_id}"
        ),
        InlineKeyboardButton(
            "🕳 Хранилище",
            callback_data=f"eco_storage:{owner_id}"
        )
    ],
    [
        InlineKeyboardButton(
            "🛒 Магазин",
            callback_data=f"eco_shop:{owner_id}"
        ),    
        InlineKeyboardButton(
            "🧬 Апгрейды",
            callback_data=f"eco_upgrades:{owner_id}"
        ),
    ],
    [
        InlineKeyboardButton(
            "🏆 Топ",
            callback_data=f"eco_top:{owner_id}"
        )
    ],
])

def get_actions_keyboard(owner_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎣 Рыбалка", callback_data=f"eco_fish:{owner_id}")
        ,
        
            InlineKeyboardButton("⛏️ Шахта", callback_data=f"eco_mine:{owner_id}")
        ],
        [
            InlineKeyboardButton("🌲 Лес", callback_data=f"eco_forest:{owner_id}")
        ,
        
            InlineKeyboardButton("⚔️ Сражение", callback_data=f"eco_battle:{owner_id}")
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"eco_main_menu:{owner_id}")
        ],
    ])

def get_goback_keyboard(owner_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"eco_main_menu:{owner_id}")
        ],
    ])
