from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

from routers.dashboard import router as dash_router
from routers.neko_chat import router as chat_router
from routers.darkness_auth import router as darkness_auth_router
from routers.darkness_direct import router as darkness_direct_router
from routers.darkness_reminders import router as darkness_reminders_router

app.include_router(dash_router)
app.include_router(chat_router)
app.include_router(darkness_auth_router)
app.include_router(darkness_direct_router)
app.include_router(darkness_reminders_router)

@app.get("/")
async def root():
    return {"ok": True, "msg": "Такой страницы еще нет"}
