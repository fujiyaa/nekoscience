


import time
from ....external.localapi import read_file_neko
from .options import *



def format_match_title(match_id: str, match: dict) -> str:
    creator = match.get("creator") or {}
    member = match.get("member") or {}

    creator_name = creator.get("osu_name", "Неизвестно")
    member_name = member.get("osu_name", "...")

    short_id = match_id[-5:]

    if member_name == "...":
        return f"[{short_id}] {creator_name} vs {member_name} (ожидает противника)"

    config = match.get("config", {})

    hours = int(config.get("time", 0))

    created_at = int(match.get("created_at", 0))

    duration = hours * 3600
    end_time = created_at + duration

    remaining = max(0, int(end_time - time.time()))

    h = remaining // 3600
    m = (remaining % 3600) // 60

    return f"[{short_id}] {creator_name} vs {member_name} ({h}ч {m}м)"

def get_all_matches(matches: dict) -> list[str]:
    result = []

    sorted_matches = sorted(
        matches.items(),
        key=lambda item: item[1].get("created_at", 0),
        reverse=True
    )

    for match_id, match in sorted_matches:

        state = match.get("state", {})

        if state.get("finished"):
            continue

        result.append(
            format_match_title(match_id, match)
        )

        if len(result) >= 100:
            break

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

        result.append(format_match_title(match_id, match))

    return result

async def find_matches_by_user(user_id: str):
    found = []
   
    response = await read_file_neko(m_file)
    matches = response.get("current", {})

    for _match_id, match in matches.items():
        creator = match.get("creator", {})
        member = match.get("member", {})

        is_creator = str(creator.get("osu_id")) == user_id
        is_member = str(member.get("osu_id")) == user_id        

        if is_creator or is_member:
            found.append(match)

    return found