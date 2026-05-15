


import time



def format_match_title(match: dict) -> str:
    creator = match.get("creator") or {}
    member = match.get("member") or {}

    creator_name = creator.get("osu_name", "Неизвестно")
    member_name = member.get("osu_name", "...")

    if member_name == "...":
        return f"{creator_name} vs {member_name} (ожидает противника)"

    config = match.get("config", {})
    timers = match.get("timers", {})

    hours = int(config.get("time", 0))

    created_at = int(match.get("created_at", 0))

    duration = hours * 3600
    end_time = created_at + duration

    remaining = max(0, int(end_time - time.time()))

    h = remaining // 3600
    m = (remaining % 3600) // 60

    return f"{creator_name} vs {member_name} ({h}ч {m}м)"

def get_all_matches(matches: dict) -> list[str]:
    result = []

    for match_id, match in matches.items():

        state = match.get("state", {})

        if state.get("finished"):
            continue

        result.append(format_match_title(match))

    return result

def get_user_matches(
    matches: dict,
    active_matches: list[str]
) -> list[str]:

    result = []

    for match_id in active_matches:

        match = matches.get(match_id)

        if not match:
            continue

        state = match.get("state", {})

        if state.get("finished"):
            continue

        result.append(format_match_title(match))

    return result