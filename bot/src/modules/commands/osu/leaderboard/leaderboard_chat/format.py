


import math



def format_dynamic(value, max_significant=2):
    if value == 0:
        return "0"

    abs_val = abs(value)

    if abs_val >= 1:
        formatted = f"{value:,.2f}"
    else:
        zeros = int(-math.floor(math.log10(abs_val)))
        precision = zeros + max_significant - 1
        formatted = f"{value:.{precision}f}"

    return formatted.rstrip("0").rstrip(".")

def format_caption(i, country_code, name, prop_value, prop_pre, prop_post):
    if isinstance(prop_value, float):
        value = format_dynamic(prop_value)
    else:
        value = f"{prop_value:,}"
    return f"{i}. {country_code} {name} - {prop_pre}{value}{prop_post}"

def format_stats(user):
    stats = user.get("statistics") or {}
    grade_counts = stats.get("grade_counts") or {}
    monthly_counts = user.get("monthly_playcounts") or []

    level_current = stats.get("level", {}).get("current", 0)
    level_progress = stats.get("level", {}).get("progress", 0)
    level = float(f"{level_current}.{level_progress}")

    hours = stats.get("play_time", 0) // 3600
    playcount = stats.get("play_count", 0)
    medals = len(user.get("user_achievements") or [])

    ssh_count = grade_counts.get("ssh", 0)
    ss_count = grade_counts.get("ss", 0)
    sh_count = grade_counts.get("sh", 0)
    s_count = grade_counts.get("s", 0)
    a_count = grade_counts.get("a", 0)

    total_hits = stats.get("total_hits", 0)
    count_300 = stats.get("count_300", 0)
    count_100 = stats.get("count_100", 0)
    count_50 = stats.get("count_50", 0)
    count_miss = stats.get("count_miss", 0)
    miss_ratio = total_hits / count_miss if count_miss > 0 else 0

    first_places = user.get('scores_first_count') or 0

    minutes_per_play = (hours * 60) / playcount if playcount > 0 and hours > 0 else 0
    hits_per_hour = total_hits / hours if hours > 0 else 0

    max_count = max((item.get('count', 0) for item in monthly_counts), default=0)
    avg_count_per_month = sum(item.get('count', 0) for item in monthly_counts) / len(monthly_counts) if monthly_counts else 0

    total_pp = stats.get("pp", 0)
    num_months = len(monthly_counts)
    avg_pp_per_month = total_pp / num_months if num_months > 0 else 0

    hpp = round(total_hits / max(playcount, 1), 2)

    peak_rank = user.get("rank_highest", {}).get("rank", 0)
    join_date = (user.get("join_date") or "1970-01-01").split("T")[0]

    return {
        "name": user.get("username", "Unknown"),
        "rank": stats.get("global_rank") or 0,
        "rank_perc": stats.get("global_rank_percent") or 0,
        "country_rank": stats.get("country_rank") or 0,
        "peak_rank": peak_rank,
        "pp": total_pp,
        "acc": stats.get("hit_accuracy", 0),
        "level": level,
        "hours": hours,
        "playcount": playcount,
        "avg_count_per_month": avg_count_per_month,
        "ranked_score": stats.get("ranked_score", 0),
        "total_score": stats.get("total_score", 0),
        "total_hits": total_hits,
        "ssh": ssh_count,
        "ss": ss_count,
        "sh": sh_count,
        "s": s_count,
        "a": a_count,
        "max_combo": stats.get("maximum_combo", 0),
        "medals": medals,
        "join_date": join_date,
        "replays": stats.get("replays_watched_by_others", 0),
        "avg_pp_per_month": avg_pp_per_month,
        "max_count": max_count,
        "followers": user.get('follower_count', 0),
        "mapping": user.get('mapping_follower_count', 0),
        "maps": user.get('beatmap_playcounts_count', 0),
        "posts": user.get('post_count', 0),
        "hpp": hpp,
        "first_places": first_places,
        "country_code": user.get('country_code', 'XX'),
        "count_300": count_300,
        "count_100": count_100,
        "count_50": count_50,
        "count_miss": count_miss,
        "miss_ratio": miss_ratio,
        "hits_per_hour": hits_per_hour,
        "minutes_per_play": minutes_per_play
    }