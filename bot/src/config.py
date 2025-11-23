from telegram.error import NetworkError, BadRequest
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from telegram import InputFile, Update, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, LinkPreviewOptions
from telegram.constants import ChatAction
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from io import BytesIO
import traceback
import io, time, html, json, lxml.html, glob, random, logging, tempfile, asyncio, aiohttp, aiofiles, colorsys, atexit, requests
import os, re, tempfile
from telegram import MessageEntity, InputTextMessageContent
from telegram.helpers import escape_markdown
from datetime import date
from dotenv import load_dotenv
 
import sys


from decimal import Decimal, getcontext
from statistics import mean
import zipfile
import subprocess
from osrparse import Replay
from typing import List, Dict
from typing import Optional

from pydub import AudioSegment  
from pathlib import Path    

import sqlite3

load_dotenv()

dev_flag = "1"

from pathlib import Path


from translations import TRANSLATIONS as TR
from longtext import *


BOT_DIR = Path(__file__).parent

IMAGES_DIR = BOT_DIR / "images"
CHALLENGES_DIR = BOT_DIR / "challenges"
COVERS_DIR = BOT_DIR / "cache/covers"
AVATARS_DIR = BOT_DIR / "cache/avatars"
BEATMAPS_DIR = BOT_DIR / "cache/beatmaps"
BEATMAPS_DIR_AUDIO = BOT_DIR / "cache/beataudio"
GROUPS_DIR = BOT_DIR / "stats/groups"
SCORES_DIR = BOT_DIR / "scores"
CARDS_DIR = BOT_DIR / "cache/cards"
OSZ_DIR = BOT_DIR / "cache/osz"

IMAGES_JSON = BOT_DIR / "images/images_data.json"
ALL_UPDATES_LOG = BOT_DIR / "logs/all_updates.log"
DELETED_MESSAGES_LOG = BOT_DIR / "logs/deleted_messages.log"
COUNT_ME_FILE = BOT_DIR / "cooldowns/count_me_times.json"
BLACKLIST_FILE = BOT_DIR / "settings/blacklist.txt"
POSITIVE_FILE = BOT_DIR / "settings/positive_words.txt"
NEGATIVE_FILE = BOT_DIR / "settings/negative_words.txt"           
RATINGS_FILE = BOT_DIR / "settings/ratings.json"
USERS_SKILLS_FILE = BOT_DIR / "stats/skills/skills.json"
COOLDOWN_FILE = BOT_DIR / "cooldowns/cooldowns.json"
QUEUE_FILE = BOT_DIR / "stats/queue.txt"
FLAG_FILE = BOT_DIR / "stats/flags/worker_running.flag"
STATS_BEATMAPS = BOT_DIR / "stats/beatmaps"
USER_SETTINGS_FILE = BOT_DIR / "settings/user_settings.json"
OSU_ID_CACHE_FILE = BOT_DIR / "settings/osu_user_cache.json"

GRAPH_PNG = BOT_DIR / 'cards/rank.png'

MAX_CONCURRENT_REQUESTS = 10

COOLDOWN_RENDER_COMMANDS = 30
COOLDOWN_HELP_COMMAND = 3
COOLDOWN_MP3_COMMAND = 30
COOLDOWN_WEEK_SECONDS = 24 * 60 * 60
COOLDOWN_GIFS_COMMANDS = 4
COOLDOWN_PICS_COMMANDS = 10
COOLDOWN_RECENT_FIX_COMMAND = 10
COOLDOWN_CARD_COMMAND = 10
COOLDOWN_DEV_COMMANDS = 1
COOLDOWN_STATS_COMMANDS = 3
COOLDOWN_RS_COMMAND = 30
RS_BUTTONS_TIMEOUT = 30
URL_SCAN_TIMEOUT = 2
LXML_TIMEOUT = 0.3

OSU_CLIENT_ID = 35505
OSU_CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET") 
TARGET_CHAT_ID = -1002502301063 
TARGET_CHAT_ID = -1002401281941 
# CLIPS_TOPIC_ID = 4 
CLIPS_TOPIC_ID = 21039 
ARCHER_BOT = 7115118941
LUCKY_TOPIC_ID = 3196
LUCKY_TOPIC_ID = 29617
LUCKY_DICE_EMOJI = "🎰" 
CHANCE_DICE = 0.20 
CHANCE_PIC = 0.10
tier_points_plus = {1: 75, 2: 50, 3: 25, 4: 5}
tier_points_minus = {1: 30, 2: 25, 3: 15, 4: 10}
COL1, COLMID, COL2 = 14, 12, 14
SOURCE_TOPIC_ID = 37686
CHALLENGE_TOPIC_ID = 85927          
TARGET_FORWARD_TOPIC_ID = None
CACHE_TTL = 24 * 60 * 60 * 365 * 100 # 100 лет 
CACHE_TTL_AUDIO = 24 * 60 * 60 * 30

ADMINS = {1803166423}

TEMP_DIR = os.path.join(tempfile.gettempdir(), "beatmap_temp")
USERS_FILE = os.path.join(CHALLENGES_DIR, "users.json")
POINTS_FILE = os.path.join(CHALLENGES_DIR, "points.json")

user_sessions = {}
remove_tasks = {}
message_authors = {}

os.makedirs(SCORES_DIR, exist_ok=True)
os.makedirs(BOT_DIR / "stats", exist_ok=True)
os.makedirs(BOT_DIR / "stats/flags", exist_ok=True)
os.makedirs(BOT_DIR / "stats/skills", exist_ok=True)
os.makedirs(BOT_DIR / "stats/data", exist_ok=True)
os.makedirs(STATS_BEATMAPS, exist_ok=True)
os.makedirs(GROUPS_DIR, exist_ok=True)
os.makedirs(BOT_DIR / "cooldowns", exist_ok=True)
os.makedirs(BOT_DIR / "settings", exist_ok=True)
os.makedirs(BOT_DIR / "logs", exist_ok=True)
os.makedirs(BEATMAPS_DIR, exist_ok=True)
os.makedirs(BEATMAPS_DIR_AUDIO, exist_ok=True)
os.makedirs(CHALLENGES_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(AVATARS_DIR, exist_ok=True)
os.makedirs(CARDS_DIR, exist_ok=True)
os.makedirs(OSZ_DIR, exist_ok=True)

OSU_USER_REGEX = re.compile(r"osu\.ppy\.sh/users/(\d+)")
OSU_SCORE_REGEX = re.compile(r"osu\.ppy\.sh/scores/(\d+)")
COOLDOWN_LINKS_IN_CHAT = 5


VALID_MODS = {"DT", "NC", "HT", "DC", "HD", "FL", "HR", "EZ", "SD", "PF", "NF", "DA", "NM"}  # пример
INVALID_MODS_COMBINATIONS = [
    {"DT", "HT"},
    {"HR", "EZ"},
    {"HR", "DA"},
    {"DA", "EZ"},
    {"SD", "PF"},
]
ABSOLUTELY_FORBIDDEN = {"NM"}
sessions_simulate = {}  

semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)  


getcontext().prec = 28

OSU_MAP_REGEX = re.compile(
    r"https?://osu\.ppy\.sh/beatmapsets/\d+#\w+/(\d+)"
)

# if sys.platform.startswith("win"): 
   

# else:  # Linux
    

dev_flag = os.getenv("DEV_FLAG", "0")  # default "0"
TOKEN = os.getenv("DTOKEN") if dev_flag == "1" else os.getenv("TOKEN")
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", None)
OSU_SESSION = os.getenv("OSU_SESSION", None)
LOCAL_API_URL = os.getenv("LOCAL_API_URL", None)

COOLDOWN_FARM_COMMAND = 5



# временно
BASE_DIR = Path(__file__).resolve().parents[2]  # nekoscience/
REMINDERS_DATA_FILE = BASE_DIR / "web" / "src" / "reminders" / "data" / "reminders.json"
REMINDERS_PW_FILE = BASE_DIR / "web" / "src" / "reminders" / "data" / "passwords.json"
VERIFIED_USERS_FILE = BASE_DIR / "web" / "src" / "auth" / "verified.json"
VERIFY_PENDING_FILE = BASE_DIR / "web" / "src" / "auth" / "pending.json"

GIF_BLACKS_PATH = BOT_DIR / "gifs" / "blacks" / "sticker.webm"
GIF_DOUBT_PATH = BOT_DIR / "gifs" / "doubt" / "blue-archive-otogi.mp4"