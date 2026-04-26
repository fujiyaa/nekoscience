


import traceback
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .keyboard_types import SELECT_TYPE, SELECT_DETAIL_TYPE, SELECT_FIRE_TYPE
from .....systems.translations import (
    DEFAULT_SCORES_TYPES as ST,
    DEFAULT_BUTTON_TYPES as BT
)



async def get_keyboard(
    origin_user_id: int,
    osu_username: str,
    ruleset: str = 'osu',
    keyboard_type: str = SELECT_TYPE,
    language: str = 'ru'       
) -> InlineKeyboardMarkup:

    keyboard = []

    try:
        if keyboard_type == SELECT_TYPE:
            k_type = 1
            action = 'u'

            types = [
                (action, f"{ST.get('Recent')[language]}", 'recent'),
                (action, f"{ST.get('Best')[language]}", 'best'),
                (action, f"{ST.get('Pinned')[language]}", 'pinned'),
                ('c', f"{BT.get('Cancel')[language]}", 'none'),
            ]

        elif keyboard_type == SELECT_DETAIL_TYPE:
            k_type = 2
            action = 'u'

            types = [
                (action, f"{ST.get('Recent')[language]}", 'recent'),
                (action, f"{ST.get('Best')[language]}", 'best'),
                (action, f"{ST.get('Pinned')[language]}", 'pinned'),
                ('c', f"{BT.get('Cancel')[language]}", 'none'),
            ]

        elif keyboard_type == SELECT_FIRE_TYPE:
            k_type = 0
            action = 'f'

            types = [
                (action, f"{ST.get('1m')[language]}", '1m'),
                (action, f"{ST.get('2m')[language]}", '2m'),
                (action, f"{ST.get('3m')[language]}", '3m'),
                ('c', f"{BT.get('Cancel')[language]}", 'none'),
            ]

        else:
            raise ValueError("Unknown keyboard_type")

        for act, text, value in types:

            x = f'{act}:{origin_user_id}:{osu_username}:{value}:{ruleset}:{k_type}'
            callback_data = f'average1:{x}'

            if len(callback_data.encode("utf-8")) > 64:
                raise ValueError("callback_data too long")

            keyboard.append([
                InlineKeyboardButton(
                    text,
                    callback_data=callback_data
                )
            ])
            
        return InlineKeyboardMarkup(keyboard)
    
    except Exception:
        traceback.print_exc()
        return None