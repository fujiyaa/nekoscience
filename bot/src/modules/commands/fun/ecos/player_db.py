


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

        coins INTEGER NOT NULL DEFAULT 0,

        fish_level INTEGER NOT NULL DEFAULT 1,
        mine_level INTEGER NOT NULL DEFAULT 1,

        fish_xp INTEGER NOT NULL DEFAULT 0,
        mine_xp INTEGER NOT NULL DEFAULT 0,

        last_fish INTEGER NOT NULL DEFAULT 0,
        last_mine INTEGER NOT NULL DEFAULT 0,
                
        fish_tool_level INTEGER NOT NULL DEFAULT 1,
        mine_tool_level INTEGER NOT NULL DEFAULT 1,

        fish_luck_level INTEGER NOT NULL DEFAULT 1,
        mine_luck_level INTEGER NOT NULL DEFAULT 1
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
    (telegram_id, telegram_name, coins)
    VALUES (?, ?, 0)
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
            (fish_level + mine_level) as total_level
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
        user_id, fish_level, mine_level, total = row

        body += (
            f"{place}. {user_id}\n"
            f"   🎣 {fish_level} | ⛏️ {mine_level}\n"
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
            coins = 0,

            fish_level = 1,
            fish_xp = 0,

            mine_level = 1,
            mine_xp = 0,
                
            fish_tool_level = 1,
            mine_tool_level = 1,
                
            fish_luck_level = 1,
            mine_luck_level = 1
        WHERE telegram_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()