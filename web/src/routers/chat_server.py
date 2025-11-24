from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import datetime
import os
import re
import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))

from utils import localapi

app = FastAPI()

if not os.getenv("DEV_FLAG", "0"):
    app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myangelfujiya.ru"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"] 
)
else:
    app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"] 
)

active_connections = []

MAX_HISTORY = 3

LATEST_CLIENT_VERSION = "0.3.8-beta"

# CHAT_HISTORY_FILE = "chat_history.json"
# CHAT_LOG_FILE = "chat_log.txt"
# SERVER_LOG_FILE = "server_full_log.txt"
# VERIFIED_CODES_FILE = "verified_codes.json"

VERIFIED_TOOLTIP = "Настоящий неконейм"
DEFAULT_TOOLTIP = "Неподтвержденный неконейм"

AVATAR_URL_OSU = "https://raw.githubusercontent.com/fujiyaa/osu-expansion-neko-science/refs/heads/main/chat_icons/osu-avatar.png"
AVATAR_URL_TG = "https://raw.githubusercontent.com/fujiyaa/osu-expansion-neko-science/refs/heads/main/chat_icons/telegram-avatar.png"
AVATAR_URL_QUESTION = "https://raw.githubusercontent.com/fujiyaa/osu-expansion-neko-science/refs/heads/main/chat_icons/guest-avatar.png"

file_v = "file_chat_verified"
file_h = "file_chat_history"

async def _fetch(key: str):
        path = os.getenv(key)
        if not path:
            return {}
        resp = await localapi.read_file_neko(key)
        data = resp.get("current", {})
        return data if isinstance(data, dict) else {}

async def get_history():
    return await _fetch(file_h)

async def check_user_verified(code: str):
    verified = await _fetch(file_v)    
    return verified.get(code, {}).get("osu_username")



async def append_to_history(username: str, message: str, timestamp: str):
    response = await localapi.read_file_neko(file_h)
    current = response.get("current", {})
    if not isinstance(current, dict):
        current = {}

    existing_ids = sorted(int(k) for k in current.keys() if k.isdigit())

    new_id = existing_ids[-1] + 1 if existing_ids else 1

    current[str(new_id)] = {
        "username": username,
        "message": message,
        "timestamp": timestamp
    }

    if len(current) > MAX_HISTORY:
        last_messages = [current[str(k)] for k in existing_ids[-(MAX_HISTORY-1):]]
        last_messages.append(current[str(new_id)]) 

        await localapi.remove_from_file_neko(file_h, list(current.keys()))

        for idx, msg in enumerate(last_messages, start=1):
            await localapi.insert_to_file_neko(file_h, {str(idx): msg})
    else:
        await localapi.insert_to_file_neko(file_h, {str(new_id): current[str(new_id)]})

    return True

def sanitize_message(raw_text: str) -> str:
    clean_text = re.sub(r"<.*?>", "", raw_text)
    clean_text = (clean_text
        .replace("<", "")
        .replace(">", "")
        .replace('"', "'")
    )
    clean_text = re.sub(r"[\x00-\x1f\x7f]", "", clean_text)
    clean_text = clean_text.strip()[:300]

    return clean_text
def sanitize_username(raw_name: str) -> str:
    clean_name = re.sub(r"<.*?>", "", raw_name)
    clean_name = re.sub(r"[\x00-\x1f\x7f]", "", clean_name)
    clean_name = clean_name.replace("<", "").replace(">", "")
    clean_name = clean_name.strip()[:32]

    return clean_name

def log_server_event(msg: str):
    timestamp = datetime.datetime.utcnow().isoformat()
    line = f"[{timestamp}] {msg}\n"
    with open(SERVER_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())

@app.websocket("/chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    username = None
    try:
        auth_text = await websocket.receive_text()
        auth = json.loads(auth_text)

        input_name = auth.get("username", "Unknown")
        client_version = auth.get("version", "0.0.0")

        real_name = await check_user_verified(input_name)
        active_connections.append((websocket, real_name))

        history = await get_history()
        
        for msg_id, msg in history.items():
            input_name = msg.get("username")

            real_name = await check_user_verified(input_name)

            if real_name:
                msg["username"] = real_name 
                msg["tooltip"] = VERIFIED_TOOLTIP
                msg["avatar"] = AVATAR_URL_OSU
            else:
                msg["username"] = input_name      
                msg["tooltip"] = DEFAULT_TOOLTIP  
                msg["avatar"] = AVATAR_URL_QUESTION
            msg["type"] = "message"

            await websocket.send_text(json.dumps(msg))

        if client_version != LATEST_CLIENT_VERSION:
            await websocket.send_text(json.dumps({
                "type": "update_available",
                "latest_version": LATEST_CLIENT_VERSION,
                "message": f"Новая версия {LATEST_CLIENT_VERSION} доступна, список изменений https://github.com/fujiyaa/osu-expansion-neko-science !"
            }))

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") in ("heartbeat", "auth"):
                continue                        
            
            message = sanitize_message(msg.get("message", ""))
            input_name = sanitize_username(msg.get("username", "Unknown")) 
            real_name = await check_user_verified(input_name)
            timestamp = datetime.datetime.utcnow().isoformat()
            
            if await append_to_history(input_name, message, timestamp):  
                if real_name:
                    msg["username"] = real_name 
                    msg["tooltip"] = VERIFIED_TOOLTIP
                    msg["avatar"] = AVATAR_URL_OSU
                else:
                    msg["username"] = input_name      
                    msg["tooltip"] = DEFAULT_TOOLTIP  
                    msg["avatar"] = AVATAR_URL_QUESTION      
                msg["message"] = message          

                await broadcast(msg)


    except WebSocketDisconnect:
        if (websocket, username) in active_connections:
            active_connections.remove((websocket, username))
            log_server_event(f"{username} left the chat")


async def broadcast(msg: dict):
    text = json.dumps(msg)
    for ws, _ in active_connections:
        try:
            await ws.send_text(text)
        except:
            log_server_event(f"Failed to send message to {ws}")


if __name__ == "__main__":
    for f in [CHAT_HISTORY_FILE, CHAT_LOG_FILE, SERVER_LOG_FILE]:
        if not os.path.exists(f):
            with open(f, "w", encoding="utf-8") as _:
                pass

    uvicorn.run(app, host="127.0.0.1", port=8010)

