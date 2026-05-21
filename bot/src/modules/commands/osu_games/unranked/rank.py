


def get_player_rank(data: dict, osu_id: str) -> int:
    osu_id = str(osu_id)

    ranking = sorted(
        (
            (str(uid), int(user.get("points", {}).get("current", 0)))
            for uid, user in data.items()
        ),
        key=lambda x: x[1],
        reverse=True
    )

    for i, (uid, _) in enumerate(ranking, 1):
        if uid == osu_id:
            return i

    raise ValueError(f"Player {osu_id} not found in ranking")

def get_top_players(
    data: dict,
    limit: int = 10
) -> list[str]:

    ranking = sorted(
        (
            (
                str(uid),
                user.get("osu", {}).get("username", "Unknown"),
                int(user.get("points", {}).get("current", 0))
            )
            for uid, user in data.items()
        ),
        key=lambda x: x[2],
        reverse=True
    )

    result = []

    for i, (_, username, points) in enumerate(ranking[:limit], 1):
        result.append(
            f"{i}. {username} - 🏆{points}"
        )

    return result