


import traceback
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .keyboard_types import SELECT_TYPE
from .....systems.translations import (
    DEFAULT_SCORES_TYPES as ST,
    DEFAULT_BUTTON_TYPES as BT
)



async def get_keyboard(
        origin_user_id: int,
        osu_username:   str,
        ruleset:        str = 'osu',
        keyboard_type:  str = SELECT_TYPE,
        language:       str = 'ru'       
    ) -> InlineKeyboardMarkup:
    
    keyboard = []

    try:
        if keyboard_type == SELECT_TYPE:
            types = [
                ('u', f"{ST.get('Recent')[language]}", 'recent'),
                ('u', f"{ST.get('Best')  [language]}", 'best'),
                ('u', f"{ST.get('Pinned')[language]}", 'pinned'),
                ('c',   f"{BT.get('Cancel')[language]}", 'none'),
            ]

            for action, text, scores_type in types:

                x = f'{action}:{origin_user_id}:{osu_username}:{scores_type}:{ruleset}'
                callback_data = f'average1:{x}'
                callback_len = len(callback_data.encode("utf-8"))

                if callback_len > 64:
                    raise ValueError(
                        f'callback_data too long ({callback_len} bytes, max 64)'
                    )
                
                keyboard.append([
                    InlineKeyboardButton(
                        text,
                        callback_data=f'average1:{x}'
                    )
                ])
                
            return InlineKeyboardMarkup(keyboard)
    except Exception:
        traceback.print_exc()
        return None        
