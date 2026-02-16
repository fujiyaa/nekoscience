


import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ......actions.messages import safe_send_message
from ......systems.cooldowns import check_user_cooldown

from ......external.localapi import read_file_neko

from ..buttons import get_keyboard

from config import COOLDOWN_CHALLENGE_COMMANDS

MAX_ATTEMPTS = 1

d_file = "file_daily_challenge"



async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    user_id = str(update.effective_user.id)    
    can_run = await check_user_cooldown(
        command_name="challenge_leaderboard",
        user_id=user_id,
        cooldown_seconds=COOLDOWN_CHALLENGE_COMMANDS,
        update=update,
        context=context,
        warn_text=f"⏳ Подождите {COOLDOWN_CHALLENGE_COMMANDS} секунд"        
    )    
    if not can_run or update.effective_user.username is None:
        return
    
    for _ in range(MAX_ATTEMPTS):
        try:
            response = await read_file_neko(d_file)
            data = response.get("current", {})

            for osu_id in data:                
                user = data[osu_id]   

            leaderboard_current = []
            leaderboard_total = []

            for osu_id, user in data.items():
                osu_name = user["osu"]["username"]
                tg_name = user["telegram"]["username"]
                points = user["v1"]["points"]

                current_score = points.get("current_season", 0)

                total_score = current_score + points.get("previous_seasons", 0)

                leaderboard_current.append({
                    "osu": osu_name,
                    "tg": tg_name,
                    "score": current_score
                })

                leaderboard_total.append({
                    "osu": osu_name,
                    "tg": tg_name,
                    "score": total_score
                })

            leaderboard_current = sorted(leaderboard_current, key=lambda x: x["score"], reverse=True)[:10]
            leaderboard_total   = sorted(leaderboard_total, key=lambda x: x["score"], reverse=True)[:3]

            medals = ["🥇", "🥈", "🥉"]
            text = "<b>⭐ Этот сезон:</b>\n\n"
            for i, entry in enumerate(leaderboard_current, 1):
                prefix = medals[i-1] if i <= 3 else f"  <b>{i}</b> "
                osu_url = f"https://osu.ppy.sh/users/{entry['osu']}"
                tg_url  = f"https://t.me/{entry['tg']}"
                text += f"{prefix} <a href='{osu_url}'>{entry['osu']}</a> (<a href='{tg_url}'>{entry['tg']}</a>) - {entry['score']} очков\n"

            text += "\n\n<b>🏆 Топ за все время</b>\n\n"
            for i, entry in enumerate(leaderboard_total, 1):
                prefix = medals[i-1] if i <= 3 else f"{i}."
                osu_url = f"https://osu.ppy.sh/users/{entry['osu']}"
                tg_url  = f"https://t.me/{entry['tg']}"
                text += f"{prefix} <a href='{osu_url}'>{entry['osu']}</a> (<a href='{tg_url}'>{entry['tg']}</a>) - {entry['score']} очков\n"    

            reply_markup = get_keyboard("leaderboard")

            await safe_send_message(
                update,
                text,
                parse_mode="HTML",
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )            

            return
        except Exception:
            traceback.print_exc()
    