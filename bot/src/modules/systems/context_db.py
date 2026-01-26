


import sqlite3
import time
import json
from typing import Optional, Dict, Any

DB_PATH = "message_cache.db"



def init_db():
    """
    Инициализация таблицы и индексов.
    Таблица хранит все сообщения с TTL и metadata в JSON.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS message_cache (
            is_supergroup INTEGER,
            chat_id INTEGER,
            topic_id INTEGER,
            message_id INTEGER,
            metadata TEXT,
            timestamp INTEGER,
            ttl INTEGER,
            PRIMARY KEY (chat_id, topic_id, message_id)
        )
        """)

        # индекс по чату и топику для быстрого поиска последних сообщений
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_cache_chat_topic_time
        ON message_cache(chat_id, topic_id, timestamp);
        """)

        # индекс для обычных чатов без топика
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_cache_chat_time_no_topic
        ON message_cache(chat_id, timestamp);
        """)

        conn.commit()


def cache_message(
    is_supergroup: bool,
    chat_id: int,
    topic_id: Optional[int],
    message_id: int,
    metadata: Dict[str, Any],
    ttl: int = 30 * 24 * 3600,
    timestamp: Optional[int] = None
):
    """
    Сохраняет сообщение в кеш с TTL.
    """
    if timestamp is None:
        timestamp = int(time.time())

    metadata_json = json.dumps(metadata, ensure_ascii=False)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO message_cache (
                is_supergroup, chat_id, topic_id, message_id, metadata, timestamp, ttl
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            1 if is_supergroup else 0,
            chat_id,
            topic_id,
            message_id,
            metadata_json,
            timestamp,
            ttl
        ))
        conn.commit()


def find_recent(
    chat_id: int,
    topic_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Ищет последнее сообщение в этом чате/топике, игнорируя TTL.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if topic_id is None:
            cur.execute("""
                SELECT * FROM message_cache
                WHERE chat_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (chat_id,))
        else:
            cur.execute("""
                SELECT * FROM message_cache
                WHERE chat_id = ? AND topic_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (chat_id, topic_id))

        row = cur.fetchone()
        if not row:
            return None

        return {
            "is_supergroup": bool(row["is_supergroup"]),
            "chat_id": row["chat_id"],
            "topic_id": row["topic_id"],
            "message_id": row["message_id"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "timestamp": row["timestamp"],
            "ttl": row["ttl"]
        }


def find_by_message_id(message_id: int) -> Optional[Dict[str, Any]]:
    """
    Ищет сообщение по message_id, игнорируя TTL.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM message_cache
            WHERE message_id = ?
            LIMIT 1
        """, (message_id,))
        row = cur.fetchone()
        if not row:
            return None

        return {
            "is_supergroup": bool(row["is_supergroup"]),
            "chat_id": row["chat_id"],
            "topic_id": row["topic_id"],
            "message_id": row["message_id"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "timestamp": row["timestamp"],
            "ttl": row["ttl"]
        }


def cleanup_expired():
    """
    Удаляет все сообщения, срок действия которых истёк.
    """
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM message_cache WHERE timestamp + ttl < ?", (now,))
        conn.commit()


init_db()