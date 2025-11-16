from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import aiohttp
import json
from pathlib import Path

import os 
from dotenv import load_dotenv
load_dotenv()

dev_flag = os.getenv("DEV_FLAG", "0")  # default "0"
OSU_CLIENT_ID = os.getenv("OSU_CLIENT_ID_BOT_AUTH", None)
OSU_CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET_BOT_AUTH", None)
OSU_REDIRECT_URI = os.getenv("OSU_REDIRECT_URI_BOT_AUTH", None)

USER_FILE = Path("/var/www/myangelfujiya/users.json")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def load_user_data():
    if not USER_FILE.exists():
        USER_FILE.touch()
        return {}
    with open(USER_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_user_data(data):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


@app.get("/")
async def index():
    return RedirectResponse("/tryauth")

@app.get("/tryauth")
async def tryauth(request: Request, error: str = None):
    return templates.TemplateResponse("tryauth.html", {"request": request, "error": error})

@app.post("/check_telegram")
async def check_telegram(request: Request, tg_nick: str = Form(...)):
    data = load_user_data()
    if tg_nick in data:
        return templates.TemplateResponse(
            "tryauth.html", 
            {"request": request, "error": "Такой ник Telegram уже зарегистрирован, если это ваш никнейм, используйте команду бота /reset!"}
        )
    # Редирект на login с GET
    return RedirectResponse(f"/login?tg_nick={tg_nick}", status_code=303)

@app.get("/login")
async def login(tg_nick: str):
    url = (
        "https://osu.ppy.sh/oauth/authorize"
        f"?client_id={OSU_CLIENT_ID}"
        f"&redirect_uri={OSU_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
        f"&state={tg_nick}"
    )
    return RedirectResponse(url)

@app.get("/oauth/callback")
async def osu_callback(request: Request, code: str = None, state: str = None):
    tg_nick = state 
    if not code:
        return templates.TemplateResponse("tryauth.html", {"request": request, "error": "osu не вернул code"})

    async with aiohttp.ClientSession() as session:
        async with session.post("https://osu.ppy.sh/oauth/token", json={
            "client_id": OSU_CLIENT_ID,
            "client_secret": OSU_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": OSU_REDIRECT_URI
        }) as resp:
            token_data = await resp.json()

    access_token = token_data.get("access_token")
    if not access_token:
        return templates.TemplateResponse("tryauth.html", {"request": request, "error": "Не удалось получить токен"})

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://osu.ppy.sh/api/v2/me",
            headers={"Authorization": f"Bearer {access_token}"}
        ) as resp:
            user_data = await resp.json()

    username = user_data.get("username")
    osu_id = str(user_data.get("id"))

    data = load_user_data()
    # Проверка, что этот osu аккаунт не зарегистрирован ранее
    for tg, osu in data.items():
        if osu.get("osu_id") == osu_id:
            return templates.TemplateResponse(
                "tryauth.html",
                {"request": request, "error": "Этот osu аккаунт уже зарегистрирован!"}
            )

    data[tg_nick] = {
        "osu_id": osu_id,
        "name": username
    }
    save_user_data(data)

    return templates.TemplateResponse("sucsess.html", {
        "request": request,
        "username": username,
        "osu_id": osu_id
    })
