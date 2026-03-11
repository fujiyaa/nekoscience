from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio

router = APIRouter()

UPDATE_FILE = "file_side_update" 

active_connections = []
connections_lock = asyncio.Lock()

async def _fetch_update():
    import os, pathlib, sys
    sys.path.append(str(pathlib.Path(__file__).parent.parent))
    from utils import localapi

    path = os.getenv(UPDATE_FILE)
    if not path:
        return {}
    resp = await localapi.read_file_neko(UPDATE_FILE)
    data = resp.get("current", {})

    return data if isinstance(data, dict) else {}

async def broadcast(msg: dict):
    text = json.dumps(msg)
    to_remove = []
    async with connections_lock:
        for ws in active_connections:
            try:
                await ws.send_text(text)
            except:
                to_remove.append(ws)
        for ws in to_remove:
            active_connections.remove(ws)

@router.websocket("/side/update")
async def websocket_update_endpoint(websocket: WebSocket):
    await websocket.accept()
    async with connections_lock:
        active_connections.append(websocket)
    
    try:
        auth_text = await websocket.receive_text()
        try:
            auth = json.loads(auth_text)
        except:
            await websocket.send_text(json.dumps({"type": "error", "message": "invalid_auth"}))
            await websocket.close()
            return

        client_version = auth.get("version", "0.0.0")

        update_info = await _fetch_update()
        server = update_info.get('server', {})
        version = server.get('version')
        prefix = server.get('prefix', '')
        features = server.get('features', '')

        if version and not compare_versions(client_version, version):
            await websocket.send_text(json.dumps({
                "type": "update_available",
                "latest_version": version,
                "message": f"{prefix}{features}"
            }))
        else:
            await websocket.send_text(json.dumps({
                "type": "up_to_date",
                "latest_version": version
            }))

        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break

    finally:
        async with connections_lock:
            if websocket in active_connections:
                active_connections.remove(websocket)

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