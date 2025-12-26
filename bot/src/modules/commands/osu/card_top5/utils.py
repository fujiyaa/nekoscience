


from datetime import datetime, timezone



def format_mods(mods):
    result = []

    for mod in mods or []:
        if isinstance(mod, dict):
            acronym = mod.get("acronym", "")
            speed = mod.get("settings", {}).get("speed_change")

            if speed:
                result.append(f"{acronym}-{speed}x")
            else:
                result.append(acronym)

        elif isinstance(mod, str):
            result.append(mod)

    return result

def time_ago(iso_time: str) -> str:
    past = datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    delta = now - past
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''} ago"

    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"

    days = hours // 24
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''} ago"

    months = days // 30
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''} ago"

    years = months // 12
    return f"{years} year{'s' if years != 1 else ''} ago"
