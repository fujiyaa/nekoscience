from fastapi import APIRouter, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import json
import os

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pathlib import Path

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/darkness/reminders")

BASE_DIR = Path(__file__).resolve().parents[3]  # nekoscience/
DATA_FILE = BASE_DIR / "web" / "src" / "reminders" / "data" / "reminders.json"
PASSWORD_FILE = BASE_DIR / "web" / "src" / "reminders" / "data" / "passwords.json"

MAX_REMINDERS_PER_USER = 10

files_to_create = {
    DATA_FILE: [],
    PASSWORD_FILE: {}
}

for filename, initial_content in files_to_create.items():
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            if initial_content is not None:
                json.dump(initial_content, f, ensure_ascii=False, indent=2)

@router.get("/")
async def reminders(request: Request):
    return templates.TemplateResponse("darkness_reminders.html", {"request": request})



@router.post("/password")
async def login(request: Request):
    data = await request.json()
    password = data.get("password")
    if not password:
        raise HTTPException(status_code=400, detail="Пароль не указан")

    try:
        with open(PASSWORD_FILE, "r", encoding="utf-8") as f:
            passwords = json.load(f)  
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Файл паролей не найден")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Ошибка формата файла паролей")

    if password in passwords.values():
        return {"user": password} 
    else:
        raise HTTPException(status_code=401, detail="Неверный пароль")


@router.post("/save")
async def save_reminder(request: Request):
    data = await request.json()
    print("[DEBUG] /save получены данные:", data)
    required_keys = ("user", "message", "date", "time", "repeatCount")
    if not all(k in data for k in required_keys):
        raise HTTPException(status_code=400, detail="Некорректные данные")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reminders = json.load(f)

    user_count = sum(1 for r in reminders if r.get("user") == data["user"])

    if user_count >= MAX_REMINDERS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"Превышено максимальное количество {MAX_REMINDERS_PER_USER} напоминаний для одного пользователя"
        )

    reminders.append(data)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)

    return {"status": "ok", "message": "Напоминание сохранено"}


@router.get("/list")
def list_reminders(user: str = None):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reminders = json.load(f)

    if user:
        reminders = [r for r in reminders if r.get("user") == user]

    return JSONResponse(content=reminders)


@router.delete("/delete")
def delete_reminder(user: str, message: str, date: str, time: str):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reminders = json.load(f)

    new_reminders = [
        r for r in reminders
        if not (
            r.get("user") == user and
            r.get("message") == message and
            r.get("date") == date and
            r.get("time") == time
        )
    ]

    if len(new_reminders) == len(reminders):
        raise HTTPException(status_code=404, detail="Напоминание не найдено")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_reminders, f, ensure_ascii=False, indent=2)

    return {"status": "ok", "message": "Напоминание удалено"}
