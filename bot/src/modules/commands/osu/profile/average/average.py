


import traceback
from telegram import Update

from .....actions.messages import safe_edit_query, safe_edit_message
from .buttons import get_keyboard

from .....systems.translations import DEFAULT_COMMAND_TEMPLATE as T
from .keyboard_types import SELECT_TYPE, SELECT_DETAIL_TYPE # SELECT_FIRE_TYPE



async def average(
    update: Update, 
    username, 
    language,
    detail_type: bool = False
):
    try:
        query = update.callback_query

        if detail_type == "ppfire":
            k_type = "select_fire"
        else:
            k_type = SELECT_DETAIL_TYPE if detail_type else SELECT_TYPE

        reply_markup = await get_keyboard(
            origin_user_id = update.effective_user.id,
            osu_username = username,
            ruleset = 'osu',
            keyboard_type = k_type,
            language = language
        )

        if reply_markup is None:
            raise ValueError(
                f'reply_markup is None'
            )
        
        if query is not None:        
            await safe_edit_query(
                query,
                text=f"`{T.get('Select...')[language]}`",
                parse_mode="Markdown",
                reply_markup=reply_markup,
                disable_web_page_preview=False,
            )
        else:
            await safe_edit_message(
                update.effective_message,
                text=f"`{T.get('Select...')[language]}`",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )

    except Exception:
        traceback.print_exc() 
        
        try:
            await safe_edit_query(
                query,
                text=f"`{T.get('Error...')[language]}`",
                parse_mode="Markdown",
                disable_web_page_preview=False,
            )

        except Exception:
            traceback.print_exc()
