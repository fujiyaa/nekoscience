from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import json, datetime, secrets, os, re, httpx

router = APIRouter()

LATEST_CLIENT_VERSION = "0.3.4-beta"
MAX_HISTORY = 100

CHAT_HISTORY_FILE = "chat/cache/chat_history.json"
CHAT_LOG_FILE = "chat/cache/chat_log.txt"
SERVER_LOG_FILE = "chat/cache/server_full_log.txt"
VERIFIED_CODES_FILE = "chat/data/verified_codes.json"

DEFAULT_TOOLTIP = "Неподтвержденный неконейм"

AVATAR_URL_OSU = "https://raw.githubusercontent.com/fujiyaa/osu-expansion-neko-science/refs/heads/main/chat_icons/osu-avatar.png"
AVATAR_URL_TG = "https://raw.githubusercontent.com/fujiyaa/osu-expansion-neko-science/refs/heads/main/chat_icons/telegram-avatar.png"
AVATAR_URL_QUESTION = "https://raw.githubusercontent.com/fujiyaa/osu-expansion-neko-science/refs/heads/main/chat_icons/guest-avatar.png"

active_connections = []

files_to_create = {
    CHAT_HISTORY_FILE: None,
    CHAT_LOG_FILE: None,
    SERVER_LOG_FILE: None
}

for filename, initial_content in files_to_create.items():
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            if initial_content is not None:
                json.dump(initial_content, f, ensure_ascii=False, indent=2)

def sanitize_message(raw_text: str) -> str:
    clean_text = re.sub(r"<.*?>", "", raw_text)
    clean_text = clean_text.replace("<", "").replace(">", "").replace('"', "'")
    clean_text = re.sub(r"[\x00-\x1f\x7f]", "", clean_text)
    return clean_text.strip()[:300]

def sanitize_username(raw_name: str) -> str:
    clean_name = re.sub(r"<.*?>", "", raw_name)
    clean_name = re.sub(r"[\x00-\x1f\x7f]", "", clean_name)
    clean_name = clean_name.replace("<", "").replace(">", "")
    return clean_name.strip()[:32]

def log_server_event(msg: str):
    timestamp = datetime.datetime.utcnow().isoformat()
    line = f"[{timestamp}] {msg}\n"
    with open(SERVER_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    print(line.strip())

def append_to_chat_history(msg: dict):
    try:
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    except:
        history = []

    history.append(msg)
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    line = f"[{msg.get('timestamp', datetime.datetime.utcnow().isoformat())}] {msg.get('username')}: {msg.get('message')}\n"
    with open(CHAT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

def load_verified_codes():
    try:
        with open(VERIFIED_CODES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_verified_codes(data):
    with open(VERIFIED_CODES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def broadcast(msg: dict):
    text = json.dumps(msg)
    for ws, _ in active_connections:
        try:
            await ws.send_text(text)
        except:
            log_server_event(f"Failed to send message to {ws}")

@router.websocket("/neko-science/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    username = None
    try:
        auth_text = await websocket.receive_text()
        auth = json.loads(auth_text)
        input_nick_or_code = auth.get("username", "Unknown")
        client_version = auth.get("version", "0.0.0")

        verified_codes = load_verified_codes()

        if input_nick_or_code in verified_codes:
            user_data = verified_codes[input_nick_or_code]
            username = user_data.get("username", "Unknown")
            tooltip = user_data.get("tooltip", DEFAULT_TOOLTIP)
        else:
            username = input_nick_or_code
            tooltip = DEFAULT_TOOLTIP

        if client_version != LATEST_CLIENT_VERSION:
            await websocket.send_text(json.dumps({
                "type": "update_available",
                "latest_version": LATEST_CLIENT_VERSION,
                "message": f"Новая версия {LATEST_CLIENT_VERSION} доступна!"
            }))

        active_connections.append((websocket, username))

        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except:
            history = []

        for msg in history:
            code = msg.get("username")
            user_info = verified_codes.get(code)
            if user_info:
                msg["username"] = user_info.get("username", code)
                msg["tooltip"] = user_info.get("tooltip", DEFAULT_TOOLTIP)
            else:
                msg["tooltip"] = DEFAULT_TOOLTIP
            await websocket.send_text(json.dumps(msg))

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") in ("heartbeat", "auth"):
                continue

            input_name = msg.get("username")
            if input_name in verified_codes:
                user_info = verified_codes[input_name]
                msg["tooltip"] = user_info.get("tooltip", DEFAULT_TOOLTIP)
                msg["username"] = user_info["username"]
            else:
                msg["tooltip"] = DEFAULT_TOOLTIP

            # аватар
            if msg["tooltip"] == "Настоящий неконейм (osu!)":
                msg["avatar"] = AVATAR_URL_OSU
            elif msg["tooltip"] == "Настоящий неконейм (тг)":
                msg["avatar"] = AVATAR_URL_TG
            else:
                msg["avatar"] = AVATAR_URL_QUESTION

            msg["message"] = sanitize_message(msg.get("message", ""))
            msg["username"] = sanitize_username(msg.get("username", "Unknown"))

            append_to_chat_history(msg)
            await broadcast(msg)

    except WebSocketDisconnect:
        if (websocket, username) in active_connections:
            active_connections.remove((websocket, username))
            log_server_event(f"{username} left the chat")

OSU_CLIENT_ID = 45317
OSU_CLIENT_SECRET = "pEop0AZ6t7IpNTtx3t5v74ik9WvIivazH7ZgcZPS"
OSU_REDIRECT_URI = "https://myangelfujiya.ru/neko-science/callback"

@router.get("/neko-science/auth-start")
async def auth_start():
    html = """<html>...твой HTML тут...</html>"""
    return HTMLResponse(html)

@router.get("/neko-science/login")
async def login():
    url = (
        f"https://osu.ppy.sh/oauth/authorize"
        f"?client_id={OSU_CLIENT_ID}"
        f"&redirect_uri={OSU_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
    )
    return RedirectResponse(url)

@router.get("/neko-science/auth-start")
async def auth_start():
    html = """
    <html>
      <head>
        <meta charset="utf-8">
        <title>NekoScience Auth</title>
        <style>
          body {
            background: linear-gradient(135deg, #1f1c2c, #928dab);
            color: #fff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
          }
          .container {
            background: rgba(0,0,0,0.6);
            padding: 40px 60px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
          }
          h1 {
            margin-bottom: 20px;
            font-size: 32px;
          }
          p {
            margin: 0 0 30px 0;
            font-size: 18px;
          }
          a button {
            padding: 12px 28px;
            font-size: 18px;
            font-weight: bold;
            color: #fff;
            background: #f97171;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.3s;
          }
          a button:hover {
            background: #ff5c5c;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Добро пожаловать в neko-science</h1>
          <p>Авторизуйтесь через osu! чтобы получить подтвержденный ник</p>
          <a href="/neko-science/login"><button>Авторизовать</button></a>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(html)


@router.get("/neko-science/login")
async def login():
    url = (
        f"https://osu.ppy.sh/oauth/authorize"
        f"?client_id={OSU_CLIENT_ID}"
        f"&redirect_uri={OSU_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
    )
    return RedirectResponse(url)

@router.get("/neko-science/callback")
async def callback(code: str):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://osu.ppy.sh/oauth/token",
            data={
                "client_id": OSU_CLIENT_ID,
                "client_secret": OSU_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": OSU_REDIRECT_URI
            }
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return HTMLResponse("<h1>Ошибка при получении токена</h1>")

        headers = {"Authorization": f"Bearer {access_token}"}
        user_resp = await client.get("https://osu.ppy.sh/api/v2/me", headers=headers)
        user_data = user_resp.json()
        username = user_data.get("username")

    verified_codes = load_verified_codes()
    if username in verified_codes:
        code_value = verified_codes[username]
    else:
        while True:        
            code_value = secrets.token_urlsafe(12)
            if code not in verified_codes:
                break
        verified_codes[code_value] = {
            "username": username,
            "tooltip": "Настоящий неконейм (osu!)"
        }
        save_verified_codes(verified_codes)

    # Перенаправляем на страницу завершения авторизации с кодом
    return RedirectResponse(f"/neko-science/auth-finish?username={username}&code={code_value}")

@router.get("/neko-science/auth-finish")
async def auth_finish(username: str, code: str):
    html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <title>Авторизация завершена</title>
        <style>
          body {{
            background: linear-gradient(135deg, #1f1c2c, #928dab);
            color: #fff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
          }}
          .container {{
            background: rgba(0,0,0,0.6);
            padding: 30px 50px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 8px 20px rgba(0,0,0,0.4);
          }}
          h2 {{
            margin-bottom: 20px;
            font-size: 28px;
          }}
          .code-box {{
            background: rgba(255,255,255,0.1);
            padding: 12px 20px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 20px;
            color: #f9f871;
            display: inline-block;
            margin-top: 10px;
          }}
          p {{
            margin: 0;
            font-size: 16px;
          }}
          a.button {{
            margin-top: 20px;
            display: inline-block;
            padding: 10px 24px;
            background: #f97171;
            color: #fff;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            transition: background 0.3s;
          }}
          a.button:hover {{
            background: #ff5c5c;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <h2>Нереальный успех</h2>
          <p>Твой код:</p>
          <div class="code-box">{code}</div>
          <p>Вставь его в поле "неконейм" в настройках чата.</p>
          <a href="https://osu.ppy.sh/" class="button">Закрыть</a>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(html)



   


