from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import datetime
import os
import re
import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from utils import localapi

router = APIRouter()
active_connections = []

file_v = "file_chat_verified"
file_h = "file_chat_history"
file_u = "file_chat_update"

MAX_HISTORY = 50

VERIFIED_TOOLTIP = "Настоящий неконейм"
DEFAULT_TOOLTIP = "Неподтвержденный неконейм"
AVATAR_URL_OSU = "https://raw.githubusercontent.com/fujiyaa/osu-expansion-neko-science/refs/heads/main/chat_icons/osu-avatar.png"
AVATAR_URL_QUESTION = "https://raw.githubusercontent.com/fujiyaa/osu-expansion-neko-science/refs/heads/main/chat_icons/guest-avatar.png"


async def _fetch(key: str):
        path = os.getenv(key)
        if not path:
            return {}
        resp = await localapi.read_file_neko(key)
        data = resp.get("current", {})
        return data if isinstance(data, dict) else {}

async def get_history():
    return await _fetch(file_h)

async def get_update():
    return await _fetch(file_u)

async def check_user_verified(code: str):
    verified = await _fetch(file_v)    
    return verified.get(code, {}).get("username")

async def append_to_history(username: str, message: str, timestamp: str):
    response = await localapi.read_file_neko(file_h)
    current = response.get("current", {})
    if not isinstance(current, dict):
        current = {}

    existing_ids = sorted(int(k) for k in current.keys() if k.isdigit())

    new_id = existing_ids[-1] + 1 if existing_ids else 1

    await localapi.insert_to_file_neko(file_h, {
        str(new_id): {
            "username": username,
            "message": message,
            "timestamp": timestamp
        }
    })

    existing_ids.append(new_id)
    if len(existing_ids) > MAX_HISTORY:
        oldest_id = existing_ids[0]
        await localapi.remove_from_file_neko(file_h, [str(oldest_id)])

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

@router.websocket("/chat/ws")
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

        sorted_history = sorted(
            ((int(k), v) for k, v in history.items() if k.isdigit()),
            key=lambda x: x[0]
        )
        
        for msg_id, msg in sorted_history:
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

        update = await get_update()

        s = update.get('server')
        version, features = s.get('version'), s.get('features')

        if client_version != version:
            await websocket.send_text(json.dumps({
                "type": "update_available",
                "latest_version": version,
                "message": f"Новая версия {version} доступна, список изменений: {features}"
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

async def broadcast(msg: dict):
    text = json.dumps(msg)
    for ws, _ in active_connections:
        try:
            await ws.send_text(text)
        except:
            pass
