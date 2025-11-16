from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "/var/www/myangelfujiya/darkness/reminder/reminders.json"
MAX_REMINDERS_PER_USER = 10

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

@app.get("/darkness/")
def root():
    return FileResponse("/var/www/myangelfujiya/darkness/reminder/static/index.html")


PASSWORD_FILE = "/var/www/myangelfujiya/darkness/reminder/passwords.json"

@app.post("/darkness/password")
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


@app.post("/darkness/save")
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


@app.get("/darkness/list")
def list_reminders(user: str = None):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reminders = json.load(f)

    if user:
        reminders = [r for r in reminders if r.get("user") == user]

    return JSONResponse(content=reminders)


@app.delete("/darkness/delete")
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
