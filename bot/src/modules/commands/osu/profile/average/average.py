


import traceback
from telegram import Update

from .....actions.messages import safe_edit_query
from .buttons import get_keyboard

from .....systems.translations import DEFAULT_COMMAND_TEMPLATE as T
from .keyboard_types import SELECT_TYPE



async def average(
    update: Update, 
    username, 
    language
):
    try:
        query = update.callback_query

        reply_markup = await get_keyboard(
            origin_user_id = update.effective_user.id,
            osu_username = username,
            ruleset = 'osu',
            keyboard_type = SELECT_TYPE,
            language = language
        )

        if reply_markup is None:
            raise ValueError(
                f'reply_markup is None'
            )
        
        await safe_edit_query(
            query,
            text=f"`{T.get('Select...')[language]}`",
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=False,
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
