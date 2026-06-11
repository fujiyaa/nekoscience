


import aiohttp

from telegram import Update

from config import TOKEN



async def send_rich_message(chat_id: int, markdown: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendRichMessage"

    payload = {
        "chat_id": chat_id,
        "rich_message": {
            "markdown": markdown
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()

            if not data.get("ok"):
                raise Exception(data)

            return data

async def rich_reply(
    update: Update,
    markdown: str,
    reply_markup=None,
    disable_notification=False,
    protect_content=False,
    message_effect_id=None,
):
    url = f"https://api.telegram.org/bot{TOKEN}/sendRichMessage"

    payload = {
        "chat_id": update.effective_chat.id,
        "rich_message": {
            "markdown": markdown
        }
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup.to_dict()

    if disable_notification:
        payload["disable_notification"] = True

    if protect_content:
        payload["protect_content"] = True

    if message_effect_id:
        payload["message_effect_id"] = message_effect_id

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()

            if not data.get("ok"):
                raise Exception(
                    f"sendRichMessage failed: {data}"
                )

            return data
        
async def edit_rich_message(
    update: Update,
    message_id: int,
    markdown: str,
    reply_markup=None,
):
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"

    payload = {
        "chat_id": update.effective_chat.id,
        "message_id": message_id,
        "rich_message": {
            "markdown": markdown
        }
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup.to_dict()

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()

            if not data.get("ok"):
                raise Exception(f"editRichMessage failed: {data}")

            return data