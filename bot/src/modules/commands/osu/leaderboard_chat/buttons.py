


from telegram import InlineKeyboardButton, InlineKeyboardMarkup

profile = "👤 Профиль"
ranks = "📊 Ранки"
plays = "🎮 Игры"
score = "🧮 Очки"
social = "👥 Социальная хрень"
botgames = "✴️ Игры бота"

def get_keyboard(keyboard_type: str, user_id: int):
    if keyboard_type == "select_group":
        keyboard = [
            [
                InlineKeyboardButton(profile, 
                callback_data=f"leaderboard_chat_group_profile:{user_id}"),

                InlineKeyboardButton(ranks, 
                callback_data=f"leaderboard_chat_group_ranks:{user_id}"),
            ],
            [
                InlineKeyboardButton(plays, 
                callback_data=f"leaderboard_chat_group_plays:{user_id}"),          

                InlineKeyboardButton(score, 
                callback_data=f"leaderboard_chat_group_score:{user_id}"),
            ],
            [
                InlineKeyboardButton(social, 
                callback_data=f"leaderboard_chat_group_social:{user_id}")
            ],
            [
                InlineKeyboardButton(botgames, 
                callback_data=f"leaderboard_chat_group_botgames:{user_id}")
            ],            
        ]    

    return InlineKeyboardMarkup(keyboard)
