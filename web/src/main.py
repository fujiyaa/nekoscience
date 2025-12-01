from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()

if not os.getenv("DEV_FLAG", "0"):
    app.add_middleware(
    CORSMiddleware, allow_origins=["https://myangelfujiya.ru"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"] 
)
else:
    app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, 
    allow_methods=["*"], allow_headers=["*"] 
)    

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

from routers.dashboard import router as dash_router
from routers.chat_auth import router as chat_router
from routers.chat_server import router as chat_server_router
from routers.darkness_auth import router as darkness_auth_router
from routers.darkness_direct import router as darkness_direct_router
from routers.darkness_reminders import router as darkness_reminders_router
from routers.vote_for_images import router as vote_for_images_router

app.include_router(dash_router)
app.include_router(chat_router)
app.include_router(chat_server_router)
app.include_router(darkness_auth_router)
app.include_router(darkness_direct_router)
app.include_router(darkness_reminders_router)
app.include_router(vote_for_images_router)

@app.get("/")
async def root():
    return {"ok": True, "msg": "Такой страницы еще нет"}
