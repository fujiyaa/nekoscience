


import math



def format_dynamic(value, max_significant=2):
    if value == 0:
        return "0"

    abs_val = abs(value)

    if abs_val >= 1:
        formatted = f"{value:,.2f}"
    else:
        # считаем сколько нулей после точки
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
    stats = user["statistics"]
    level = float(f"{stats['level']['current']}.{stats['level']['progress']}")
    hours = stats["play_time"] // 3600
    playcount = stats.get("play_count", 0)
    medals = len(user["user_achievements"])
    
    ssh_count = stats.get("grade_counts", {}).get("ssh", 0)
    ss_count = stats.get("grade_counts", {}).get("ss", 0)
    sh_count = stats.get("grade_counts", {}).get("sh", 0)
    s_count = stats.get("grade_counts", {}).get("s", 0)
    a_count = stats.get("grade_counts", {}).get("a", 0)

    monthly = user.get('monthly_playcounts', [])

    total_hits = stats.get("total_hits", 0)
    count_300 = stats.get("count_300", 0)
    count_100 = stats.get("count_100", 0)
    count_50 = stats.get("count_50", 0)
    count_miss = stats.get("count_miss", 0)
    miss_ratio = 0

    if count_miss > 0 and total_hits > 0:
        miss_ratio = total_hits / count_miss

    if playcount > 0 and hours > 0:
        minutes_per_play = (hours * 60) / playcount
    else:
        minutes_per_play = 0

    if hours > 0:
        hits_per_hour = total_hits / hours
    else:
        hits_per_hour = 0


    if monthly:
        max_count = max(item['count'] for item in monthly)
    else:
        max_count = 0
    
    # if best_pp:
    #     pp_values = [item['pp'] for item in best_pp]
    #     pp_diff = max(pp_values) - min(pp_values)
    #     pp_avg_all = sum(pp_values) / len(pp_values)
    # else:
    #     pp_values = []
    #     pp_diff = 0
    #     pp_avg_all = 0

    # anime_bg_counter = 0
    # not_anime_bg_counter = 0

    # pp_by_month = defaultdict(list)
    # for item in best_pp:
    #     month = item.get('date', str(best_pp.index(item)))[:7]  # YYYY-MM
    #     pp_by_month[month].append(item['pp'])

    #     is_anime_bg = item.get("is_anime_bg", False)

    #     if is_anime_bg:
    #         anime_bg_counter += 1
    #     else: 
    #         not_anime_bg_counter +=1

    monthly_counts = user.get('monthly_playcounts', [])
    if monthly_counts:
        avg_count_per_month = sum(item['count'] for item in monthly_counts) / len(monthly_counts)
    else:
        avg_count_per_month = 0

    total_pp = stats.get("pp", 0)
    num_months = len(user.get('monthly_playcounts', []))
    avg_pp_per_month = total_pp / num_months if num_months > 0 else 0

    hpp = round(stats.get('total_hits', 0) / max(stats.get('play_count', 1), 1), 2)

    return {
        "name": user["username"],
        "rank": stats.get("global_rank") or 0,
        "rank_perc": stats.get("global_rank_percent") or 0,
        "country_rank": stats.get("country_rank") or 0,
        "peak_rank": user["rank_highest"]["rank"] if user.get("rank_highest") else 0,
        "pp": stats.get("pp", 0),
        "acc": stats.get("hit_accuracy", 0),
        "level": level,
        "hours": hours,
        "playcount": playcount,
        "avg_count_per_month": avg_count_per_month,
        # "ranked_score": user['statistics']['ranked_score'],
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
        "join_date": user["join_date"].split("T")[0],
        "replays": stats.get("replays_watched_by_others", 0),
        # "top1_pp": best_pp[0]["pp"] if best_pp else 0,
        # "pp_avg_all": pp_avg_all,
        "avg_pp_per_month": avg_pp_per_month,
        # "pp_diff": pp_diff,
        "max_count": max_count,
        "followers": user['follower_count'],
        "mapping": user['mapping_follower_count'],
        "maps": user['beatmap_playcounts_count'],
        "posts": user['post_count'],
        "hpp": hpp,
        # "anime_bg_counter": anime_bg_counter,
        # "not_anime_bg_counter": not_anime_bg_counter,

        "country_code": user['country_code'],

        "count_300": count_300,
        "count_100": count_100,
        "count_50": count_50,
        "count_miss": count_miss,
        "miss_ratio": miss_ratio,

        "hits_per_hour": hits_per_hour,
        "minutes_per_play": minutes_per_play        
    }