


import time, tempfile, asyncio
import os, re, tempfile
from dotenv import load_dotenv 
from decimal import getcontext
from pathlib import Path
load_dotenv()

from longtext import *      # файл с длинными ответами бота


BOT_DIR = Path(__file__).parent                 
#
#   при запуске из скрипта, это та же папка где остальные папки бота
#   ..nekoscience/bot/src/ *здесь*
#   
#   если далее в комментариях сказано "Можно удалять", то имеется ввиду 
#   удалить папку и перезапустить бота полностью


SCORES_DIR = BOT_DIR / "scores_v4"
#   
#   самая важная папка
#   
#   везде где в боте используется отображение чего-то из скора, сначала сохраняется сюда
#   и только потом читается отсюда
#
#   можно удалять, или переимновать в v5, v6 и тд (и добавить в .gitignore)


COVERS_DIR = BOT_DIR / "cache/covers"          
AVATARS_DIR = BOT_DIR / "cache/avatars"
BG_LIST_DIR = BOT_DIR / "cache/card_beatmap/list"
BG_CARD_DIR = BOT_DIR / "cache/card_beatmap/card"
#
#   кеш картинок карточек, лучше хранить
#
#   в то время как сами картинки готовых карточек удаляются после отправки,
#   сами исходники (аватарки и бг карт) перезаписываются только если устарели
#
#   т.е. могут накапливаться и иногда можно удалять всю эту папку.


BEATMAPS_DIR = BOT_DIR / "cache/beatmaps"
CACHE_TTL = 24 * 60 * 60 * 365 * 100 # 100 лет 
#   
#   карты в txt формате (.osu)
#   
#   наличие карт сильно ускоряет работу, они занимают мало места
#   (примерно 1 гб на 30.000 карт)
#   уменьшение CACHE_TTL не решает никакой задачи
#
#   используются только для расчета РР и cs/ar/od...#
#   за все остальное (автор, статус и тд) отвечает кеш скоров
#   
#   если файл битый или пустой, лучше удалить один конкретный .osu


CARDS_DIR = BOT_DIR / "cache/cards"
TOP5_CARDS_DIR = BOT_DIR / "cache/top5cards"
BG_SCORE_COMPARE_DIR = BOT_DIR / "cache/card_score_compare"
#   
#   для разных готовых карточек
# 
#   должна сама очищаться если все ок


OSZ_DIR = BOT_DIR / "cache/osz"
#   
#   эти osz скачивает /music и /bg 
#   (файлы уже распакованы)
# 
#   НЕ очищается никогда, так как лучше использовать кеш
#   можно удалять иногда папку


USER_SETTINGS_FILE = BOT_DIR / "settings/user_settings.json"
#
#   файл с настройками пользователей /settings


OSU_ID_CACHE_FILE = BOT_DIR / "settings/osu_user_cache.json"
#
#   сохраняет ID для того чтобы не справшивать осу каждый раз 
#   
#   могут быть проблемы только если какой то пользователь бота удалить свой акк,
#   и осу создаст новый с таким же ID, и он попадется новому пользователю бота
#   (возможно никогда не произойдет, но если да то просто удалить этот кеш файл)


COUNT_ME_FILE = BOT_DIR / "cooldowns/count_me_times.json"
QUEUE_FILE = BOT_DIR / "stats/queue.txt"
FLAG_FILE = BOT_DIR / "stats/flags/worker_running.flag"
STATS_BEATMAPS = BOT_DIR / "stats/beatmaps"
GROUPS_DIR = BOT_DIR / "stats/groups"
#   
#   для /beatmaps
#   
#   удалять только если чтото не так с командой


COOLDOWN_FILE = BOT_DIR / "cooldowns/cooldowns.json"
USAGE_FILE = BOT_DIR / "cooldowns/cooldowns_v2.json"
#
#   подожди Х сек сообщение, а v2 не используется


IMAGES_DIR = BOT_DIR / "images"
IMAGES_JSON = BOT_DIR / "images/images_data.json"
#
#   папка с картинками для /gn


GRAPH_PNG = BOT_DIR / 'cards/assets/card_profile/graph.png'
#
#   картинка которая отображается под графиком в карточке профиля




# ==============================================================================================================
# дальше лучше ничего не менять


DELETED_MESSAGES_LOG = BOT_DIR / "logs/deleted_messages.log"
BLACKLIST_FILE = BOT_DIR / "settings/blacklist.txt"

MAX_CONCURRENT_REQUESTS = 10

COOLDOWN_WEEK_SECONDS = 24 * 60 * 60
COOLDOWN_PICS_COMMANDS = 10
RS_BUTTONS_TIMEOUT = 30
URL_SCAN_TIMEOUT = 2
LXML_TIMEOUT = 0.3

COOLDOWN_WITH_HTML_COMMANDS = 10
COOLDOWN_WITH_API_COMMANDS = 3
COOLDOWN_NO_API_COMMANDS = 1
COOLDOWN_DEV_COMMANDS = 1

COOLDOWN_MP3_COMMAND =          COOLDOWN_WITH_HTML_COMMANDS

COOLDOWN_RECENT_FIX_COMMAND =   COOLDOWN_WITH_API_COMMANDS
COOLDOWN_CARD_COMMAND =         COOLDOWN_WITH_API_COMMANDS
COOLDOWN_RS_COMMAND =           COOLDOWN_WITH_API_COMMANDS
COOLDOWN_MS_COMMAND =           COOLDOWN_WITH_API_COMMANDS
COOLDOWN_HLGAME_COMMANDS =      COOLDOWN_WITH_API_COMMANDS
COOLDOWN_UNRANKED_COMMANDS =    COOLDOWN_WITH_API_COMMANDS

COOLDOWN_LEADERBOARD_COMMANDS = COOLDOWN_NO_API_COMMANDS
COOLDOWN_CHALLENGE_COMMANDS =   COOLDOWN_NO_API_COMMANDS
COOLDOWN_HELP_COMMAND =         COOLDOWN_NO_API_COMMANDS
COOLDOWN_GIFS_COMMANDS =        COOLDOWN_NO_API_COMMANDS
COOLDOWN_STATS_COMMANDS =       COOLDOWN_NO_API_COMMANDS

COOLDOWN_MOD_VOTE =             COOLDOWN_NO_API_COMMANDS

DEFAULT_COOLDOWN_V2 = 5
ACTIONS_COOLDOWNS = {
    'telegram_bot': {
        'default': 1,
        'average': 5
    }
}

OSU_CLIENT_ID = os.getenv("OSU_CLIENT_ID")
OSU_CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET")
OSU_PROFILE_ACCESS_TOKEN = os.getenv("OSU_PROFILE_ACCESS_TOKEN")
# TARGET_CHAT_ID = -1002502301063 
TARGET_CHAT_ID = -1002401281941 
# CLIPS_TOPIC_ID = 4 
CLIPS_TOPIC_ID = 21039 
ARCHER_BOT = 7115118941
# LUCKY_TOPIC_ID = 3196
LUCKY_TOPIC_ID = 29617
LUCKY_DICE_EMOJI = "🎰" 
CHANCE_DICE = 0.30 
CHANCE_PIC = 0.25
SOURCE_TOPIC_ID = 37686
CHALLENGE_TOPIC_ID = 85927          
TARGET_FORWARD_TOPIC_ID = None

ADMINS = {1803166423}

TEMP_DIR = os.path.join(tempfile.gettempdir(), "beatmap_temp")

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
os.makedirs(COVERS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(AVATARS_DIR, exist_ok=True)
os.makedirs(CARDS_DIR, exist_ok=True)
os.makedirs(TOP5_CARDS_DIR, exist_ok=True)
os.makedirs(OSZ_DIR, exist_ok=True)
os.makedirs(BG_CARD_DIR, exist_ok=True)
os.makedirs(BG_LIST_DIR, exist_ok=True)
os.makedirs(BG_SCORE_COMPARE_DIR, exist_ok=True)

OSU_USER_REGEX = re.compile(
    r"(?:users|u)/([^/?#\s]+)",
    re.IGNORECASE
)

OSU_SCORE_REGEX = re.compile(
    r"(?:scores|score|s)/(\d+)",
    re.IGNORECASE
)

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
    r"(?:beatmapsets/\d+#\w+/|b/)(\d+)",
    re.IGNORECASE
)

OSU_MAP_REGEX_2 = re.compile(
    r"(?:beatmaps/|b/)(\d+)",
    re.IGNORECASE
)

OSU_MAPSET_REGEX = re.compile(
    r"https?://osu\.ppy\.sh/(?:beatmapsets/(\d+)(?:#\w+/\d+)?|b/(\d+))"
)

OSU_URL_REGEX = re.compile(
    r"https?://osu\.ppy\.sh/(?:beatmapsets/\d+#\w+/(?P<map_id1>\d+)|b/(?P<map_id2>\d+)|beatmapsets/(?P<set_id>\d+)|scores/(?P<score_id>\d+))"
)

# if sys.platform.startswith("win"): 
   
# else:  # Linux
    
dev_flag = "1"  # не важно 
dev_flag = os.getenv("DEV_FLAG", "0")  # default "0"
OSU_CHAT_OAUTH = os.getenv("OSU_CHAT_OAUTH", None)
TOKEN = os.getenv("DTOKEN") if dev_flag == "1" else os.getenv("TOKEN")
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY", None)
OSU_SESSION = os.getenv("OSU_SESSION", None)
LOCAL_API_URL = os.getenv("LOCAL_API_URL", None)

# временно
BASE_DIR = Path(__file__).resolve().parents[2]  # nekoscience/
REMINDERS_DATA_FILE = BASE_DIR / "web" / "src" / "reminders" / "data" / "reminders.json"
REMINDERS_PW_FILE = BASE_DIR / "web" / "src" / "reminders" / "data" / "passwords.json"
VERIFIED_USERS_FILE = BASE_DIR / "web" / "src" / "auth" / "verified.json"
VERIFY_PENDING_FILE = BASE_DIR / "web" / "src" / "auth" / "pending.json"

ALL_UPDATES_LOG = BASE_DIR / "storage" / "bot_data" / "all_updates.log"
AIMSLOP_FILE = BASE_DIR / "storage" / "bot_data" / "aimslop.txt"
SPEEDSLOP_FILE = BASE_DIR / "storage" / "bot_data" / "speedslop.txt"

GIF_BLACKS_PATH = BOT_DIR / "gifs" / "blacks" / "sticker.webm"
GIF_DOUBT_PATH = BOT_DIR / "gifs" / "doubt" / "blue-archive-otogi.mp4"

SUPPORT_STUB = '⚠️ Если эта ошибка что-то действительно ломает, перешли ее мне: @fujiya_sama'
MAX_TEXT_LENGTH = 4096 # огриничение тг

def load_ids(path):
    ids = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r"#osu/(\d+)", line)
            if match:
                ids.add(int(match.group(1)))
    return ids

AIMSLOP_IDS = load_ids(AIMSLOP_FILE)
SPEEDSLOP_IDS = load_ids(SPEEDSLOP_FILE)

START_TIME = time.time()