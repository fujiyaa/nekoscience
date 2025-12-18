


from datetime import datetime, timedelta
from collections import defaultdict

COL1, COLMID, COL2 = 14, 12, 14

def normalize_plus(text: str) -> str:
    if isinstance(text, list):
        text = "".join(text) 
    clean_text = text.replace('+', '').strip()
    return f"+{clean_text}" if clean_text else ""

def normalize_no_plus(text: str) -> str:
    if isinstance(text, list):
        text = "".join(text) 
    clean_text = text.replace('+', '').strip()
    return f"{clean_text}" if clean_text else ""

def format_blocks_percent(counter, total, per_row):
    items_raw = [(k, f"{round(v / total * 100)}%") for k, v in counter.most_common()]
    max_key_len = max(len(k) for k, _ in items_raw)
    max_val_len = max(len(val) for _, val in items_raw)

    if max_key_len > 4:
        per_row = max(1, per_row - 1)

    items = [
        f"<code>{k}:{' ' * (max_key_len - len(k) + 1)}{val.rjust(max_val_len)}</code>"
        for k, val in items_raw
    ]
    lines = [" • ".join(items[i:i+per_row]) for i in range(0, len(items), per_row)]
    return "\n".join(lines)

def format_blocks_pp(data_dict, per_row):
    items_raw = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
    max_key_len = max(len(k) for k, _ in items_raw)
    max_val_len = max(len(f"{round(v,1)}") for _, v in items_raw)

    if max_key_len > 4:
        per_row = max(1, per_row - 1)

    items = [
        f"<code>{k}:{' ' * (max_key_len - len(k) + 1)}{str(round(v, 1)).rjust(max_val_len)}</code>"
        for k, v in items_raw
    ]
    lines = [" • ".join(items[i:i+per_row]) for i in range(0, len(items), per_row)]
    return "\n".join(lines)
def country_code_to_flag(country_code: str) -> str:
    if not country_code or len(country_code) != 2:
        return ""
    
    return "".join(
        chr(0x1F1E6 + ord(char.upper()) - ord('A'))
        for char in country_code
    )
def format_stats(user, best_pp):
    stats = user["statistics"]
    level = float(f"{stats['level']['current']}.{stats['level']['progress']}")
    hours = stats["play_time"] // 3600
    medals = len(user["user_achievements"])
    ss_count = stats.get("grade_counts", {}).get("ss", 0)
    s_count = stats.get("grade_counts", {}).get("s", 0)
    a_count = stats.get("grade_counts", {}).get("a", 0)
    monthly = user.get('monthly_playcounts', [])

    if monthly:
        max_count = max(item['count'] for item in monthly)
    else:
        max_count = 0
    
    if best_pp:
        pp_values = [item['pp'] for item in best_pp]
        pp_diff = max(pp_values) - min(pp_values)
        pp_avg_all = sum(pp_values) / len(pp_values)
    else:
        pp_values = []
        pp_diff = 0
        pp_avg_all = 0

    pp_by_month = defaultdict(list)
    for item in best_pp:
        month = item.get('date', str(best_pp.index(item)))[:7]  # YYYY-MM
        pp_by_month[month].append(item['pp'])

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
        "peak_rank": user["rank_highest"]["rank"] if user.get("rank_highest") else 0,
        "pp": stats.get("pp", 0),
        "acc": stats.get("hit_accuracy", 0),
        "level": level,
        "hours": hours,
        "playcount": stats.get("play_count", 0),
        "avg_count_per_month": avg_count_per_month,
        "ranked_score": user['statistics']['ranked_score'],
        "ranked_score": stats.get("ranked_score", 0),
        "total_score": stats.get("total_score", 0),
        "total_hits": stats.get("total_hits", 0),
        "ss": ss_count,
        "s": s_count,
        "a": a_count,
        "max_combo": stats.get("maximum_combo", 0),
        "medals": medals,
        "join_date": user["join_date"].split("T")[0],
        "replays": stats.get("replays_watched_by_others", 0),
        "top1_pp": best_pp[0]["pp"] if best_pp else 0,
        "pp_avg_all": pp_avg_all,
        "avg_pp_per_month": avg_pp_per_month,
        "pp_diff": pp_diff,
        "max_count":max_count,
        "followers":user['follower_count'],
        "mapping":user['mapping_follower_count'],
        "maps":user['beatmap_playcounts_count'],
        "posts":user['post_count'],
        "hpp":hpp,
    }

def row(val1, mid, val2, higher_is_better=True, suffix="", preffix: str = None, fmt="{:,}", is_date=False):
    def format_val(v):
        if is_date:
            return str(v)
        try:
            n = float(v)
        except:
            return str(v)

        if n.is_integer():
            return f"{int(n):,}{suffix}"
        else:
            return fmt.format(n) + suffix

    left, right = format_val(val1), format_val(val2)

    try:
        if is_date:
            n1 = datetime.fromisoformat(val1)
            n2 = datetime.fromisoformat(val2)
        else:
            n1 = float(val1)
            n2 = float(val2)

        if preffix:
            left = f"{preffix}{left}"
            right = f"{preffix}{right}"

        if n1 != n2:
            better_left = (n1 > n2) if higher_is_better else (n1 < n2)
            if better_left:
                left = f"{left} <"
                right = f"  {right}"
            else:
                left = f"{left}  "
                right = f"> {right}"
        else:
            left = f"{left}  "
            right = f"  {right}"
    except:
        pass

    return f"{left:>{COL1}}| {mid:^{COLMID}} |{right:<{COL2}}"

def make_header(name1, name2):
    header = f"{name1:>{COL1}} | {'osu!':^{COLMID}} | {name2:<{COL2}}"
    sep = f"{'-'*COL1}+{'-'*(COLMID+2)}-{'-'*COL2}"
    return header, sep

def format_osu_date(date_str: str, today: bool = True) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    dt += timedelta(hours=3)
    if today:
        return f'{dt.strftime("%H:%M")}MSK'
    else:
        return dt.strftime("%d.%m.%Y")
    
def seconds_to_hhmmss(seconds: float) -> str:
    total_seconds = int(round(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"