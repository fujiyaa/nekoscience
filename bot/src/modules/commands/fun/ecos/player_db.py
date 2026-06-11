


import sqlite3

from telegram import MessageEntity
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .constants import *
from .buttons import *



def init_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        telegram_name TEXT,

        coins INTEGER NOT NULL DEFAULT 727,

        fish_level INTEGER NOT NULL DEFAULT 1,
        mine_level INTEGER NOT NULL DEFAULT 1,
        forest_level INTEGER NOT NULL DEFAULT 1,
        battle_level INTEGER NOT NULL DEFAULT 1,

        fish_xp INTEGER NOT NULL DEFAULT 0,
        mine_xp INTEGER NOT NULL DEFAULT 0,
        forest_xp INTEGER NOT NULL DEFAULT 0,
        battle_xp INTEGER NOT NULL DEFAULT 0,

        last_fish INTEGER NOT NULL DEFAULT 0,
        last_mine INTEGER NOT NULL DEFAULT 0,
        last_forest INTEGER NOT NULL DEFAULT 0,
        last_battle INTEGER NOT NULL DEFAULT 0,
                
        fish_tool_level INTEGER NOT NULL DEFAULT 1,
        mine_tool_level INTEGER NOT NULL DEFAULT 1,
        forest_tool_level INTEGER NOT NULL DEFAULT 1,
        battle_tool_level INTEGER NOT NULL DEFAULT 1,

        fish_luck_level INTEGER NOT NULL DEFAULT 1,
        mine_luck_level INTEGER NOT NULL DEFAULT 1,
        forest_luck_level INTEGER NOT NULL DEFAULT 1,
        battle_luck_level INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory_items (
        telegram_id INTEGER NOT NULL,
        item_id TEXT NOT NULL,
        amount INTEGER NOT NULL DEFAULT 0,

        PRIMARY KEY (telegram_id, item_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS storage_items (
        telegram_id INTEGER NOT NULL,
        item_id TEXT NOT NULL,
        amount INTEGER NOT NULL DEFAULT 0,

        PRIMARY KEY (telegram_id, item_id)
    )
    """)

    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(DB_PATH)


def ensure_user(user_id: int, user_name: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users
    (telegram_id, telegram_name)
    VALUES (?, ?)
    """, (user_id, user_name))

    cur.execute("""
    UPDATE users
    SET telegram_name = ?
    WHERE telegram_id = ?
    """, (user_name, user_id))

    conn.commit()
    conn.close()


def get_top_players(limit=10):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            telegram_name,
            fish_level,
            mine_level,
            forest_level,
            battle_level,
            (fish_level + mine_level + forest_level + battle_level) as total_level
        FROM users
        ORDER BY total_level DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()

    conn.close()

    return rows[:20]

async def show_top_players(query, owner_id):

    top = get_top_players()

    header = "🏆 Топ игроков\n\n"

    body = ""

    for place, row in enumerate(top, start=1):
        user_id, fish_level, mine_level, forest_level, battle_level, total = row

        body += (
            f"{place}. {user_id}\n"
            f"   🎣 {fish_level} | ⛏️ {mine_level} | 🌲 {forest_level} | ⚔️ {battle_level}\n"
            f"   всего уровней: {total}\n\n"
        )

    full_text = header + body

    entities = [
        MessageEntity(
            type="expandable_blockquote",
            offset=len(header),
            length=tg_len(body)
        )
    ]

    await query.edit_message_text(
        full_text,
        entities=entities,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Назад",
                    callback_data=f"eco_main_menu:{owner_id}"
                )
            ]
        ])
    )

def tg_len(text: str) -> int:
            return len(text.encode("utf-16-le")) // 2

def add_coins(user_id: int, amount: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET coins = coins + ?
    WHERE telegram_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()

def reset_balance(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET coins = 0
    WHERE telegram_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

def get_balance(user_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT coins
    FROM users
    WHERE telegram_id = ?
    """, (user_id,))

    row = cur.fetchone()

    conn.close()

    return row[0] if row else 0


def add_storage_item(user_id: int, item_id: str, amount: int = 1):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO storage_items (telegram_id, item_id, amount)
    VALUES (?, ?, ?)
    ON CONFLICT(telegram_id, item_id)
    DO UPDATE SET amount = amount + excluded.amount
    """, (user_id, item_id, amount))

    conn.commit()
    conn.close()

def add_inventory_item(user_id: int, item_id: str, amount: int = 1):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO inventory_items (telegram_id, item_id, amount)
    VALUES (?, ?, ?)
    ON CONFLICT(telegram_id, item_id)
    DO UPDATE SET amount = amount + excluded.amount
    """, (user_id, item_id, amount))

    conn.commit()
    conn.close()


def get_user_field(user_id: int, field: str, default=0):
    conn = get_conn()
    cur = conn.cursor()

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
        return default

    return row[0]

def reset_player(user_id):
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE users
        SET
            coins = 727,

            fish_level = 1,
            fish_xp = 0,

            mine_level = 1,
            mine_xp = 0,
                
            forest_level = 1,
            forest_xp = 0,
                
            battle_level = 1,
            battle_xp = 0,
                
            fish_tool_level = 1,
            mine_tool_level = 1,
            forest_tool_level = 1,
            battle_level = 1,
                
            fish_luck_level = 1,
            mine_luck_level = 1,
            forest_luck_level = 1,
            battle_luck_level = 1
                
        WHERE telegram_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()

def add_column_if_missing(name, definition):
    conn = get_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            f"ALTER TABLE users ADD COLUMN {name} {definition}"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass

    conn.close()

def migrate_add_forest():
    
    add_column_if_missing(
        "forest_level",
        "INTEGER NOT NULL DEFAULT 1"
    )

    add_column_if_missing(
        "forest_xp",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        "last_forest",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        "forest_tool_level",
        "INTEGER NOT NULL DEFAULT 1"
    )

    add_column_if_missing(
        "forest_luck_level",
        "INTEGER NOT NULL DEFAULT 1"
    )

def migrate_add_battle():
    
    add_column_if_missing(
        "battle_level",
        "INTEGER NOT NULL DEFAULT 1"
    )

    add_column_if_missing(
        "battle_xp",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        "last_battle",
        "INTEGER NOT NULL DEFAULT 0"
    )

    add_column_if_missing(
        "battle_tool_level",
        "INTEGER NOT NULL DEFAULT 1"
    )

    add_column_if_missing(
        "battle_luck_level",
        "INTEGER NOT NULL DEFAULT 1"
    )



# def convert_skill(level, xp):
#     total_xp = xp

#     for lv in range(1, level):
#         total_xp += old_xp_required(lv)

#     new_level = 1

#     while total_xp >= xp_required(new_level):
#         total_xp -= xp_required(new_level)
#         new_level += 1

#     return new_level, total_xp

# def migrate_levels():
#     conn = get_conn()
#     cur = conn.cursor()

#     cur.execute("""
#         SELECT
#             telegram_id,
#             fish_level,
#             fish_xp,
#             mine_level,
#             mine_xp
#         FROM users
#     """)

#     rows = cur.fetchall()

#     for (
#         user_id,
#         fish_level,
#         fish_xp,
#         mine_level,
#         mine_xp
#     ) in rows:

#         new_fish_level, new_fish_xp = convert_skill(
#             fish_level,
#             fish_xp
#         )

#         new_mine_level, new_mine_xp = convert_skill(
#             mine_level,
#             mine_xp
#         )

#         cur.execute("""
#             UPDATE users
#             SET
#                 fish_level = ?,
#                 fish_xp = ?,
#                 mine_level = ?,
#                 mine_xp = ?
#             WHERE telegram_id = ?
#         """, (
#             new_fish_level,
#             new_fish_xp,
#             new_mine_level,
#             new_mine_xp,
#             user_id
#         ))

#     conn.commit()
#     conn.close()

#     print("Migration complete")

# migrate_levels()