from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import aiohttp, os, json
from utils.localapi import read_file_neko, insert_to_file_neko
from datetime import datetime

templates = Jinja2Templates(directory="templates")
router = APIRouter()

file_d = "file_vote_data"

DEV = os.getenv("DEV_FLAG", "0") == "1"

if not DEV:
    OSU_CLIENT_ID = os.getenv("OSU_CLIENT_ID_VOTE_AUTH")
    OSU_CLIENT_SECRET = os.getenv("OSU_CLIENT_SECRET_VOTE_AUTH")
    OSU_REDIRECT_URI = os.getenv("OSU_REDIRECT_URI_VOTE_AUTH")
else:
    OSU_CLIENT_ID = os.getenv("DEV_OSU_CLIENT_ID_VOTE_AUTH")
    OSU_CLIENT_SECRET = os.getenv("DEV_OSU_CLIENT_SECRET_VOTE_AUTH")
    OSU_REDIRECT_URI = os.getenv("DEV_OSU_REDIRECT_URI_VOTE_AUTH")

oauth_url = (
    "https://osu.ppy.sh/oauth/authorize"
    f"?client_id={OSU_CLIENT_ID}"
    f"&redirect_uri={OSU_REDIRECT_URI}"
    f"&response_type=code"
    f"&scope=identify"
)

async def _fetch(key: str):
    path = os.getenv(key)
    if not path:
        return {}
    resp = await read_file_neko(key)
    data = resp.get("current", {})
    return data if isinstance(data, dict) else {}

@router.get("/vote")
async def vote_home(request: Request):
    return templates.TemplateResponse("vote_home.html", {"request": request})

@router.get("/vote/auth")
async def vote_auth():
    return RedirectResponse(oauth_url)

@router.get("/vote/oauth/callback")
async def vote_callback(request: Request, code: str = None):
    if not code:
        return RedirectResponse(oauth_url)

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
        return RedirectResponse(oauth_url)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://osu.ppy.sh/api/v2/me",
            headers={"Authorization": f"Bearer {access_token}"}
        ) as resp:
            user_data = await resp.json()

    username = user_data.get("username")
    user_id = user_data.get("id")

    team = user_data.get("team")
    if team and team.get("id") != 799:
        return templates.TemplateResponse("vote_home.html", {"request": request})

    return templates.TemplateResponse("vote_now.html", {
        "request": request,
        "username": username,
        "user_id": user_id
    })

@router.post("/vote/submit")
async def submit_votes(payload: str = Form(...)):
    data = json.loads(payload)
    username = data["username"]
    created_at = data["created_at"]
    votes = data["votes"]

    await insert_to_file_neko(file_d, {
        username: {
            "created_at": created_at,
            "votes": votes
        }
    })

    return {"status": "ok"}

@router.get("/vote/results")
async def vote_results(request: Request):   
    all_votes_raw = await _fetch(file_d)  
    all_votes = {}

    for username, user_data_str in all_votes_raw.items():
        if isinstance(user_data_str, str):
            all_votes[username] = json.loads(user_data_str)
        else:
            all_votes[username] = user_data_str

    stats = {}
    for user, user_data in all_votes.items():
        for vote in user_data.get("votes", []):
            img = vote["image"]
            rating = vote["rating"]
            if img not in stats:
                stats[img] = {"count": 0, "sum": 0}
            stats[img]["count"] += 1
            stats[img]["sum"] += rating

    for img, data in stats.items():
        data["average"] = round(data["sum"] / data["count"], 2) if data["count"] > 0 else 0

    return templates.TemplateResponse("vote_results.html", {
        "request": request,
        "total_users": len(all_votes),
        "stats": stats,
        "all_votes": all_votes
    })