from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import datetime
import os
import re
import sys
import pathlib
import asyncio
from collections import OrderedDict
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from utils import localapi

router = APIRouter()
id_lock, ip_lock, block_lock, connections_lock = asyncio.Lock(), asyncio.Lock(), asyncio.Lock(), asyncio.Lock()

active_connections = []
connections_per_ip = {}
connections_unverified = {}  
connections_verified = {}   
verified_cache = OrderedDict()

file_v = "file_chat_verified"
file_h = "file_chat_history"
file_u = "file_chat_update"
file_b = "file_chat_blocked"
file_a = "file_chat_adress"

MAX_CONNECTIONS_UNVERIFIED = 3
MAX_CONNECTIONS_VERIFIED = 20
MAX_HISTORY = 50
MAX_MSG_PER_5S = 5
VERIFIED_CACHE_SIZE = 1000
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

async def get_client_ip(websocket: WebSocket) -> str:
    x_forwarded_for = websocket.headers.get('x-forwarded-for')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
        return ip
    client_host, _ = websocket.client
    return client_host

async def check_user_verified(code: str):
    verified = await _fetch(file_v)
    return verified.get(code, {}).get("username")

async def check_user_verified_cached(username):
    if username in verified_cache:
        verified_cache.move_to_end(username)
        return verified_cache[username]
    real_name = await check_user_verified(username)
    verified_cache[username] = real_name
    if len(verified_cache) > VERIFIED_CACHE_SIZE:
        verified_cache.popitem(last=False)
    return real_name

async def append_to_history(username: str, message: str, timestamp: str):
    async with id_lock:
        response = await localapi.read_file_neko(file_h)
        current = response.get("current", {})

        existing_ids = sorted(int(k) for k in current.keys() if k.isdigit())
        new_id = existing_ids[-1] + 1 if existing_ids else 1

        await localapi.insert_to_file_neko(file_h, {
            str(new_id): {"username": username, "message": message, "timestamp": timestamp}
        })

        existing_ids.append(new_id)
        if len(existing_ids) > MAX_HISTORY:
            oldest_id = existing_ids[0]
            await localapi.remove_from_file_neko(file_h, [str(oldest_id)])

    return True

def sanitize_message(raw_text: str) -> str:
    import html
    clean_text = html.escape(raw_text)
    clean_text = re.sub(r'[\x00-\x1f\x7f\u200b-\u200d\uFEFF]', '', clean_text)
    return clean_text.strip()[:300]

def sanitize_username(raw_name: str) -> str:
    clean_name = re.sub(r'[\x00-\x1f\x7f\u200b-\u200d\uFEFF]', '', raw_name)
    clean_name = clean_name.replace("<", "").replace(">", "")
    return clean_name.strip()[:32]

async def is_ip_blocked(ip: str) -> bool:
    async with block_lock:
        response = await localapi.read_file_neko(file_b)
        current = response.get("current", {})
        return ip in current.values()

async def save_user_ip(username: str, ip: str):
    async with ip_lock:
        response = await localapi.read_file_neko(file_a)
        current = response.get("current", {})
        current[username] = ip
        await localapi.insert_to_file_neko(file_a, current)

async def can_connect(username: str, is_verified: bool) -> bool:
    async with connections_lock:
        if is_verified:
            return connections_verified.get(username, 0) < MAX_CONNECTIONS_VERIFIED
        else:
            return connections_unverified.get(username, 0) < MAX_CONNECTIONS_UNVERIFIED

async def register_connection(username: str, is_verified: bool):
    async with connections_lock:
        if is_verified:
            connections_verified[username] = connections_verified.get(username, 0) + 1
        else:
            connections_unverified[username] = connections_unverified.get(username, 0) + 1
        
async def unregister_connection(username: str, is_verified: bool):
    async with connections_lock:
        if is_verified:
            if username in connections_verified:
                connections_verified[username] -= 1
                if connections_verified[username] <= 0:
                    del connections_verified[username]
        else:
            if username in connections_unverified:
                connections_unverified[username] -= 1
                if connections_unverified[username] <= 0:
                    del connections_unverified[username]
        

@router.websocket("/chat/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    username = None
    msg_times = []

    try:
        auth_text = await websocket.receive_text()
        try:
            auth = json.loads(auth_text)
        except:
            await websocket.send_text(json.dumps({"type": "error", "message": "invalid_auth"}))
            await websocket.close()
            return

        username = sanitize_username(auth.get("username", "Unknown"))
        client_version = auth.get("version", "0.0.0")
        real_name = await check_user_verified_cached(username)
        display_name = real_name if real_name else username
        is_verified = real_name is not None

        client_ip = await get_client_ip(websocket)

        if await is_ip_blocked(client_ip):
            await websocket.send_text(json.dumps({"type": "error", "message": "IP в черном списке"}))
            await websocket.close()
            return
        else:
            await save_user_ip(username, client_ip)

        if not await can_connect(username, is_verified):
            await websocket.send_text(json.dumps({"type": "error", "message": "Слишком много одновременных подключений, для зарегистрированных* доступно до 20. Если это ошибка и у тебя не открыта куча вкладок с osu, сообщи: https://osu.ppy.sh/users/11596989   Это касается только чата."}))
            await websocket.close()
            return
        else:
            await register_connection(username, is_verified)


        async with connections_lock:
            active_connections.append((websocket, display_name))

        history = await get_history()
        sorted_history = sorted(
            ((int(k), v) for k, v in history.items() if k.isdigit()),
            key=lambda x: x[0]
        )
        
        users = len(connections_unverified) + len(connections_verified)
        sockets = len(active_connections)

        history_payload = []

        for msg_id, msg in sorted_history:
            name_in_history = msg.get("username")
            real_name_h = await check_user_verified_cached(name_in_history)

            if real_name_h:
                msg["username"] = real_name_h
                msg["tooltip"] = VERIFIED_TOOLTIP
                msg["avatar"] = AVATAR_URL_OSU
            else:
                msg["username"] = name_in_history
                msg["tooltip"] = DEFAULT_TOOLTIP
                msg["avatar"] = AVATAR_URL_QUESTION

            msg["type"] = "history"
            msg["total_users"] = users
            msg["total_sockets"] = sockets

            history_payload.append(msg)

        await websocket.send_text(json.dumps({"type": "history_bulk", "messages": history_payload}))


        msg = {}
        msg["type"] = "online_refresh"  
        msg["total_users"] = users

        await broadcast(msg)


        update = await get_update()
        server = update.get('server', {})
        version = server.get('version')
        prefix = server.get('prefix')
        features = server.get('features')

        if version and not compare_versions(client_version, version):
            await websocket.send_text(json.dumps({
                "type": "update_available",
                "latest_version": version,
                "message": f"{prefix}{features}"
            }))

        while True:
            try:
                data = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            try:
                msg = json.loads(data)
            except:
                continue

            if msg.get("type") in ("heartbeat", "auth"):
                continue

            now = datetime.datetime.utcnow().timestamp()
            msg_times = [t for t in msg_times if now - t < 5]
            if len(msg_times) >= MAX_MSG_PER_5S:
                continue
            msg_times.append(now)

            message = msg.get("message", "")
            if not isinstance(message, str) or len(message) > 1000:
                continue
            message = sanitize_message(message)
            input_name = sanitize_username(msg.get("username", "Unknown"))
            real_name_msg = await check_user_verified_cached(input_name)
            timestamp = datetime.datetime.utcnow().isoformat()

            await append_to_history(input_name, message, timestamp)

            if real_name_msg:
                msg["username"] = real_name_msg
                msg["tooltip"] = VERIFIED_TOOLTIP
                msg["avatar"] = AVATAR_URL_OSU
            else:
                msg["username"] = input_name
                msg["tooltip"] = DEFAULT_TOOLTIP
                msg["avatar"] = AVATAR_URL_QUESTION

            msg["type"] = "message"
            msg["message"] = message
            msg["timestamp"] = timestamp
            msg["total_users"] = len(connections_unverified) + len(connections_verified)
            msg["total_sockets"] = len(active_connections)

            await broadcast(msg)

    finally:
        if username is not None:  
            await unregister_connection(username, is_verified)
        async with connections_lock:
            active_connections[:] = [(ws, u) for ws, u in active_connections if ws != websocket]

        try:
            users = len(connections_unverified) + len(connections_verified)
            msg = {"type": "online_refresh", "total_users": users}
            await broadcast(msg)
        except Exception as e:
            print("online_refresh:", e)

async def broadcast(msg: dict):
    text = json.dumps(msg)
    to_remove = []

    async with connections_lock:
        for ws, _ in active_connections:
            try:
                await ws.send_text(text)
            except:
                to_remove.append(ws)

        if to_remove:
            active_connections[:] = [(ws, u) for ws, u in active_connections if ws not in to_remove]

def compare_versions(client_version: str, server_version: str) -> bool:
    def parse_ver(ver: str):
        ver = ver.split("-")[0].strip()
        parts = []
        for p in ver.split("."):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
        return parts

    client_parts = parse_ver(client_version)
    server_parts = parse_ver(server_version)

    max_len = max(len(client_parts), len(server_parts))
    client_parts += [0] * (max_len - len(client_parts))
    server_parts += [0] * (max_len - len(server_parts))

    for c, s in zip(client_parts, server_parts):
        if c > s:
            return True
        elif c < s:
            return False

    return True
