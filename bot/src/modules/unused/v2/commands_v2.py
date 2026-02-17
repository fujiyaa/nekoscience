


import asyncio
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from ......actions.messages import safe_send_message
from ......systems.auth import check_osu_verified
from ..buttons import get_keyboard
import temp

from config import COOLDOWN_STATS_COMMANDS, USER_SETTINGS_FILE
from ......systems.translations import DEFAULT_COMMAND_TEMPLATE as T
from ..keyboard_types import SELECT_TYPE



from ......systems.cooldowns_v2 import is_user_on_cooldown

from .commands.profile.average import get_average_markup



async def request_service_action(
    service:        str,
    action:         str,
    user_id:        int,
    command_args:   str,
    chat_id:        int,
    thread_id:      int,
    message_id:     int
):
    try:
        # cross-service cooldown system
        cooldown_seconds = is_user_on_cooldown(service, action, user_id)

        if cooldown_seconds > 0: 
            return

        # FIXME user settings
        user_settings = {}

        # FIXME check osu usernames (otiopns)
        osu_usernames = []

        if service == 'telegram_bot':
            await _request_telegram_bot_action(
                action,
                user_id,
                command_args,
                chat_id,
                thread_id,
                message_id,
                user_settings,
                osu_usernames
            )
        else:
            raise ValueError('no such service:', service)               
        
    except Exception:
        traceback.print_exc() 
        # FIXME add error response


async def _request_telegram_bot_action(
    service:        str,    
    action:         str,
    user_id:        int,
    command_args:   str,
    chat_id:        int,
    thread_id:      int,
    message_id:     int,
    user_settings:  dict,
    osu_usernames:  list,
):
    if action == 'average':
        await get_average_markup(
            service:        str,
            user_id:        int,
            command_args:   str,
            chat_id:        int,
            thread_id:      int,
            message_id:     int,
            user_settings:  dict,
            osu_usernames:  list,
        )