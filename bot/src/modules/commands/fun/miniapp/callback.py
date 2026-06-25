import json
import random, re

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from ....actions.messages import safe_send_message
from config import MINIAPP_PW_FILE


def generate_8digit_code(existing: set[str]) -> str:
    while True:
        code = f"{random.randint(0, 999999):06d}"
        if code not in existing:
            return code

def sanitize_name(name: str) -> str:
    name = re.sub(r"[\x00-\x1F\x7F]", "", name)
    return name.strip()[:20]

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    query = update.callback_query
    await query.answer(text="отправлено в личный чат (если начат чат с ботом)", show_alert=True)

    user = query.from_user
    user_id = str(user.id)
    username = user.first_name or "unknown"

    username = sanitize_name(username)

    try:
        with open(MINIAPP_PW_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    if not isinstance(data, dict):
        data = {}

    existing_codes = {v["code"] for v in data.values() if "code" in v}

    new_code = generate_8digit_code(existing_codes)

    data[user_id] = {
        "name": username,
        "code": new_code
    }

    with open(MINIAPP_PW_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await context.bot.send_message(
        chat_id=user_id,
        text=f"Твой новый код: <code>{new_code}</code>",
        parse_mode="HTML"
    )
