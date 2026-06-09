


import sqlite3
import time

from .constants import *
from .buttons import *
from .player_db import *

from .activities import *
from .items import *
from .upgrades import *



def get_last_activity(user_id: int, activity: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    field = get_last_field(activity)

    cur.execute(
        f"""
        SELECT {field}
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return 0

    return row[0]

def set_last_activity(user_id: int, activity: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    field = f"last_{activity}"
    now = int(time.time())

    cur.execute(
        f"""
        UPDATE users
        SET {field} = ?
        WHERE telegram_id = ?
        """,
        (now, user_id)
    )

    conn.commit()
    conn.close()

def add_xp(user_id: int, activity: str, xp: int):

    level_field = ACTIVITIES[activity]["level_field"]
    xp_field = ACTIVITIES[activity]["xp_field"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT {level_field}, {xp_field}
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    if not row:
        conn.close()
        return

    level, current_xp = row

    current_xp += xp

    while True:
        needed = xp_required(level)

        if current_xp < needed:
            break

        current_xp -= needed
        level += 1

    cur.execute(
        f"""
        UPDATE users
        SET
            {level_field} = ?,
            {xp_field} = ?
        WHERE telegram_id = ?
        """,
        (
            level,
            current_xp,
            user_id
        )
    )

    conn.commit()
    conn.close()


def get_progress(user_id: int, activity: str):

    level_field = ACTIVITIES[activity]["level_field"]
    xp_field = ACTIVITIES[activity]["xp_field"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT {level_field}, {xp_field}
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    if not row:
        return 1, 0, xp_required(1)

    level, xp = row

    return level, xp, xp_required(level)

def get_luck_level(user_id: int, activity_name: str):

    field_map = {
        "fish": "fish_luck_level",
        "mine": "mine_luck_level",
    }

    field = field_map[activity_name]

    return get_user_field(
        user_id,
        field,
        0
    )

def get_tool_level(user_id: int, activity_name: str):

    field_map = {
        "fish": "fish_tool_level",
        "mine": "mine_tool_level",
    }

    field = field_map[activity_name]

    return get_user_field(
        user_id,
        field,
        1
    )


def get_available_loot(activity, level):
    return [
        item for item in ACTIVITIES[activity]["loot"]
        if item["min_level"] <= level
    ]

def get_last_field(activity: str) -> str:
    return f"last_{activity}"