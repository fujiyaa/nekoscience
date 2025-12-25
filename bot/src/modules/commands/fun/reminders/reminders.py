


import json
import asyncio
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from ....systems.logging import log_all_update
from .code import generate_unique_code

from config import REMINDERS_DATA_FILE, REMINDERS_PW_FILE, user_sessions



async def reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    if update.effective_chat.type != "private":
        await update.effective_message.reply_text("Эта команда работает только в личном чате.")
        return

    user_id = str(update.effective_user.id)

    try:
        with open(REMINDERS_PW_FILE, "r", encoding="utf-8") as f:
            passwords = json.load(f)
    except FileNotFoundError:
        passwords = {}

    if user_id in passwords:
        code = passwords[user_id]
        await update.effective_message.reply_text(f"Твой пароль: `{code}` \n https://myangelfujiya.ru/darkness", parse_mode="Markdown")
        
        return

    existing_codes = set(passwords.values())
    code = generate_unique_code(existing_codes)

    passwords[user_id] = code
    with open(REMINDERS_PW_FILE, "w", encoding="utf-8") as f:
        json.dump(passwords, f, ensure_ascii=False, indent=2)

    await update.effective_message.reply_text(f"Твой пароль: `{code}`", parse_mode="Markdown")
    

# эта команда используется автоматически при новых смс
async def start_check_reminders(update, context):
    asyncio.create_task(check_reminders(update, context))

async def check_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_message.from_user:
        return

    username = update.effective_message.from_user.username
    if not username:
        return

    username_lower = username.lower()

    try:
        with open(REMINDERS_DATA_FILE, "r", encoding="utf-8") as f:
            reminders = json.load(f)
    except FileNotFoundError:
        reminders = []

    updated = False
    new_reminders = []

    for i, reminder in enumerate(reminders, start=1):
        message_lower = reminder["message"].lower()

        if f"@{username_lower}" in message_lower:

            reminder_datetime_str = f"{reminder['date']} {reminder['time']}"
            reminder_datetime = datetime.strptime(reminder_datetime_str, "%Y-%m-%d %H:%M")
            now = datetime.now()

            if now >= reminder_datetime:
                await update.effective_chat.send_message(reminder["message"])

                reminder["repeatCount"] -= 1

                if reminder["repeatCount"] > 0:
                    new_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
                    new_time = now.strftime("%H:%M")
                    reminder["date"] = new_date
                    reminder["time"] = new_time
                    new_reminders.append(reminder)
              
                updated = True
            else:
                new_reminders.append(reminder)
        else:
            new_reminders.append(reminder)

    if updated:
        with open(REMINDERS_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(new_reminders, f, ensure_ascii=False, indent=2)



