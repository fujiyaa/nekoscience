from telegram import Update
from telegram.ext import ContextTypes

from .....utils.text_format import country_code_to_flag
from .format import format_stats, format_caption
from .fetch import get_profiles
from .send import send
from .....external.localapi import read_file_neko



async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                      caption: str, 
                      prop: str, 
                      prop_pre: str, prop_post: str, 
                      top_n: int = 100,
                      value_formatter=lambda x: x):

    profiles = await get_profiles(update, context)
    stats_batch = []

    for item in profiles:
        stats = format_stats(item)
        stats_batch.append({
            prop: stats.get(prop),
            'name': stats.get('name'),
            'country_code': stats.get('country_code'),
        })

    stats_batch = sorted(
        stats_batch,
        key=lambda x: float(x.get(prop) or 0),
        reverse=True
    )

    text = f"Chat Leaderboard: {caption}\n\n"

    for i, item in enumerate(stats_batch[:top_n], start=1):
        value = value_formatter(item.get(prop))
        text += format_caption(
            i,
            country_code_to_flag(item.get('country_code', '')),
            item.get('name', 'unknown'),
            value,
            prop_pre, prop_post
        )
        text += "\n"

    await send(update, stats_batch, text)

async def leaderboard_with_json(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                      caption: str, 
                      d_file: str):

    profiles = await get_profiles(update, context)
    
    chat_ids = {item.get('id') for item in profiles}

    try:
        response = await read_file_neko(d_file)
        data = response.get("current", {})

        leaderboard_current = []
        leaderboard_total = []

        for osu_id, user in data.items():
            tg_id = user["osu"]["id"]
            if tg_id not in chat_ids:
                continue

            osu_name = user["osu"]["username"]
            tg_name = user["telegram"]["username"]
            points = user["v1"]["points"]

            if d_file != 'file_osugames_higherlower':
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
            
            else:
                current_score = points.get("best_score", 0)

                leaderboard_current.append({
                    "osu": osu_name,
                    "tg": tg_name,
                    "score": current_score
                })                

        leaderboard_current = sorted(leaderboard_current, key=lambda x: x["score"], reverse=True)[:10]
        if d_file != 'file_osugames_higherlower':
            leaderboard_total   = sorted(leaderboard_total, key=lambda x: x["score"], reverse=True)[:3]
           
        medals = ["🥇", "🥈", "🥉"]
        text = f"{caption}\n\n"
        text += "⭐ Этот сезон:\n\n"
        for i, entry in enumerate(leaderboard_current, 1):
            prefix = medals[i-1] if i <= 3 else f"  {i} "
            text += f"{prefix} {entry['osu']} ({entry['tg']}) - {entry['score']} очков\n"

        if d_file != 'file_osugames_higherlower':
            text += "\n\n🏆 Топ за все время\n\n"
            for i, entry in enumerate(leaderboard_total, 1):
                prefix = medals[i-1] if i <= 3 else f"{i}."
                text += f"{prefix} {entry['osu']} ({entry['tg']}) - {entry['score']} очков\n"   

        
        await send(update, text, text)       

    except Exception as e:
        print(e)
