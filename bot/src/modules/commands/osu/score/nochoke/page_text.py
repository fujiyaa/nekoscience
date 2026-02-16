


import html

from .....utils.text_format import country_code_to_flag



def get_text(user_data, best_scores, page=0, page_size=5):
    start = page * page_size
    end = start + page_size
    lines = []
    a, b = float(user_data["live_pp"]), float(user_data["new_total"])
    lines.append(f'<b>Total pp: {a:.2f} → {b:.2f}pp (+{(b-a):.2f})</b>')
    lines.append("")       
    for i, score in enumerate(best_scores[start:end], start=start):
        # score["weight_percent"] = 0.95 ** i

        title = html.escape(score.get("title", ""))
        version = html.escape(score.get("version", ""))
        mods = score.get("mods", [])
        mods_str = "NM" if not mods else "".join(mods)
        if score.get('lazer') == False:
            mods_str += 'CL'
        mods_str = html.escape(mods_str)        
        stars = score.get("stars", 0)
        pp_old = f"{score.get('pp_old',0):.2f}"
        pp_new = f"{score.get('pp_new',0):.2f}"
        misses = str(score.get("misses", 0))
        map_id = score.get("beatmap_id")

        url = f"https://osu.ppy.sh/beatmaps/{map_id}"
        url_2 = f"https://myangelfujiya.ru/darkness/direct?id={map_id}"

        line1 = f'<b>#{score.get("index")}</b> <a href="{url}">{title} [{version}]</a> <b>+{mods_str}</b> [{stars:.2f}★]'
        line2 = f'<a href="{url_2}">🔗</a> <code>{pp_old}</code> → <b>{pp_new}pp</b> • <i>Removed {misses}❌</i>'

        lines.append(line1)
        lines.append(line2)
        lines.append("")

    username = html.escape(user_data["username"])
    stats = user_data["statistics"]
    pp_text = f"{stats.get('pp', 0):.2f}"
    global_rank_text = f"(#{stats.get('global_rank'):,})" if stats.get("global_rank") else "(#????)"
    country_rank_text = f"{user_data['country_code']}#{stats.get('country_rank'):,}" if stats.get("country_rank") else f"{user_data['country_code']}#??"
    rank_text = f"{username}: {pp_text}pp {global_rank_text} {country_rank_text}"
    country_flag = country_code_to_flag(user_data["country_code"])
    user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
    user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'

    text = f"{user_link}\n\n" + "\n".join(lines)
    return text
