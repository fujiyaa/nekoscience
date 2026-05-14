


def get_player_rank(data: dict, osu_id: str) -> int:
    osu_id = str(osu_id)

    ranking = sorted(
        (
            (str(uid), int(user.get("v1", {}).get("points", {}).get("current", 0)))
            for uid, user in data.items()
        ),
        key=lambda x: x[1],
        reverse=True
    )

    for i, (uid, _) in enumerate(ranking, 1):
        if uid == osu_id:
            return i

    raise ValueError(f"Player {osu_id} not found in ranking")