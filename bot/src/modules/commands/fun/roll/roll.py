


import random
import string
import asyncio
import traceback
from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....systems.cooldowns import check_user_cooldown
from ....actions.messages import safe_send_message

from config import COOLDOWN_NO_API_COMMANDS
MAX_MASK_LENGTH = 128
MAX_ABS_RANGE = 10_000_000



async def start_roll(update, context):
    await log_all_update(update)
    asyncio.create_task(roll(update, context))

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        can_run = await check_user_cooldown(
            command_name="roll",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_NO_API_COMMANDS,           
            update=update,
            context=context
        )
        if not can_run:
            return
        
        default_min = 0
        default_max = 100

        arg = " ".join(context.args).strip() if context.args else ""

        if not arg:
            result = random.randint(default_min, default_max)
            text = str(result)

        elif arg.lstrip("-").isdigit():
            try:
                value = int(arg)
            except ValueError:
                value = 0

            value = max(-MAX_ABS_RANGE, min(value, MAX_ABS_RANGE))

            if value > 0:
                result = random.randint(1, value)
            elif value < 0:
                result = random.randint(value, -1)
            else:
                result = random.randint(default_min, default_max)

            text = str(result)

        else:
            arg = arg[:MAX_MASK_LENGTH]

            result_chars = []

            for ch in arg:
                if ch.isdigit():
                    result_chars.append(random.choice(string.digits))
                elif ch.isalpha():
                    if ch.islower():
                        result_chars.append(random.choice(string.ascii_lowercase))
                    else:
                        result_chars.append(random.choice(string.ascii_uppercase))
                else:
                    result_chars.append(ch)

            result = "".join(result_chars)
            text = str(result)

        await safe_send_message(update, text, parse_mode="Markdown")
                

    except Exception:
        traceback.print_exc()