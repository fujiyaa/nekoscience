from telegram import CallbackQuery

from ....fun.ecos.player_db import get_top_players_by_ids
from .....utils.text_format import country_code_to_flag
from .format import *
from .send import send



async def leaderboard_engine(
    query: CallbackQuery,
    raw_data: dict,
    action: dict
):  
    stats_batch = []
    total_batch = None

    prop=action.get("prop", "score")
    mode=action.get("provider", "profiles")

    if mode == "profiles":
        for item in raw_data:
            stats_batch.append({
                prop: item.get(prop),
                "name": item.get("name"),
                "country_code": item.get("country_code"),
            })

    elif mode.startswith("file_"):
        members = raw_data.get('members')
                
        file_data = raw_data["data"]

        leaderboard_current = []
        leaderboard_total = []

        for osu_id, user in file_data.items():
            tg_id = user["telegram"]["id"]

            if str(tg_id) not in members:
                continue

            osu_name = user["osu"]["username"]
            tg_name = user["telegram"]["username"]
            points = user["v1"]["points"]

            base = {
                "name": osu_name,
                "tg": tg_name,
                "country_code": user["osu"].get("country_code", "")
            }

            if mode.endswith("challenge"):
                current_score = points.get("current_season", 0)
                # total_score = current_score + points.get("previous_seasons", 0)

                leaderboard_current.append({
                    **base,
                    prop: current_score
                })

                # leaderboard_total.append({
                #     **base,
                #     prop: total_score
                # })

            elif mode.endswith("higherlower"):
                leaderboard_current.append({
                    **base,
                    prop: points.get("best_score", 0)
                })

        stats_batch = leaderboard_current
       
        stats_batch = sorted(
            stats_batch,
            key=lambda x: float(x.get(prop) or 0),
            reverse=True
        )

    elif mode.startswith("ecos"):
        members = raw_data.get('members')

        top_map = get_top_players_by_ids(members)

        sorted_items = sorted(
            top_map.items(),
            key=lambda x: x[1]["place"]
        )

        text = ""

        text += format_header_ecos(action.get("title", "?"))

        for tg_id, data in sorted_items[:5]:
            text += (
                f"|<code> #{data['place']} </code>  {data['telegram_name']} "
                f"| <sup>🎣 {data['fish_level']} ⛏️ {data['mine_level']} 🌲 {data['forest_level']} ⚔️ {data['battle_level']} </sup>"
                f"| <b>{data['total_level']}</b>|\n"
            )


        if len(sorted_items)>5:
            
            text += "\n\n"

            tg_id, data = sorted_items[5]
            
            row = (
                f"|<code> #{data['place']} </code>  {data['telegram_name']} "
                f"| 🎣 {data['fish_level']} ⛏️ {data['mine_level']} 🌲 {data['forest_level']} ⚔️ {data['battle_level']} "
                f"| <b>{data['total_level']}</b> |"
            )

            text += f"<details><summary>...ещё {len(sorted_items)-5}</summary>\n\n"
            
            text += row_to_header_ecos(row)

            row = format_caption(
                6,
                country_code_to_flag(item.get("country_code", "")),
                item.get("name", "unknown"),
                item.get(prop),
                action.get("pre", ""),
                action.get("post", "")
            )

            text += "</details>"


        await send(query, sorted_items, text)
        return

    if stats_batch:
        stats_batch = sorted(
            stats_batch,
            key=lambda x: float(x.get(prop) or 0),
            reverse=True
        )
    else:
        stats_batch = []



    text = ""
    text += format_header(f'{action.get("title", "?")} {action.get("extra_title", "")}')

    for i, item in enumerate(stats_batch[:5], start=1):
        value = item.get(prop)

        text += format_caption(
            i,
            country_code_to_flag(item.get("country_code", "")),
            item.get("name", "unknown"),
            value,
            action.get("pre", ""),
            action.get("post", ""),
        ) + "\n"

    text += "\n\n"   

    if len(stats_batch)>5:

        item = stats_batch[5]

        row = format_caption(
            6,
            country_code_to_flag(item.get("country_code", "")),
            item.get("name", "unknown"),
            item.get(prop),
            action.get("pre", ""),
            action.get("post", "")
        )

        text += f"<details><summary>...ещё {len(stats_batch)-5}</summary>\n\n"
        
        text += row_to_header(row)

        for i, item in enumerate(stats_batch[6:], start=7):
            value = item.get(prop)

            text += format_caption(
                i,
                country_code_to_flag(item.get("country_code", "")),
                item.get("name", "unknown"),
                value,
                action.get("pre", ""),
                action.get("post", "")
            ) + "\n"

        text += "</details>"

    await send(query, stats_batch, text)