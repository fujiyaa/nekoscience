


import sqlite3
from typing import Dict, Any, List
import random

DB_PATH = "scores_state.db"

ALLOWED_SORTS = {
    "pp": "pp",
    "sr": "sr",
    "combo": "combo_count",
    "miss": "miss_count",
}



def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS scores_state (
                id INTEGER,
                mode TEXT,
                pp REAL,
                sr REAL,
                miss_count INTEGER,
                combo_count INTEGER,
                fail_flag INTEGER,
                ranked_flag INTEGER,
                schema_version INTEGER,
                user_id INTEGER,
                PRIMARY KEY (schema_version, id, user_id)
            )
            """)

            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_pp
            ON scores_state(schema_version, mode, ranked_flag, fail_flag, pp DESC);
            """)

            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_sr
            ON scores_state(schema_version, mode, ranked_flag, fail_flag, sr DESC);
            """)

            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_combo
            ON scores_state(schema_version, mode, ranked_flag, fail_flag, combo_count DESC);
            """)

            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_miss
            ON scores_state(schema_version, mode, ranked_flag, fail_flag, miss_count ASC);
            """)

    except Exception as e:
        print(e)

def add_score(cached_entry: dict) -> bool:
    try:
        state =             cached_entry['state']
        osu_api_data =      cached_entry['osu_api_data']

        id = osu_api_data.get('id')

        if not state.get('ready') or id is None:
            #FIXME просто добавить калькулятор гдето
            print('WARN: add_score called, but cached_entry isnt ready. ID: ', id)
            return False
        
        osu_score =         cached_entry['osu_score']
        neko_api_calc =     cached_entry['neko_api_calc']
        lazer_data =        cached_entry['lazer_data']    
        meta =              cached_entry['meta']
        
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO scores_state (
                id, mode, pp, sr, miss_count, combo_count,
                fail_flag, ranked_flag, schema_version, user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(schema_version, id, user_id)
            DO UPDATE SET
                mode=excluded.mode,
                pp=excluded.pp,
                sr=excluded.sr,
                miss_count=excluded.miss_count,
                combo_count=excluded.combo_count,
                fail_flag=excluded.fail_flag,
                ranked_flag=excluded.ranked_flag
            """, (
                id,
                state.get('mode') or 'osu',
                neko_api_calc.get('pp') or 0,
                neko_api_calc.get('star_rating') or 0.0,
                osu_score.get('count_miss') or 0,
                osu_score.get('max_combo') or 0,
                osu_score.get('failed') or False,
                lazer_data.get('ranked') or False,
                meta.get('version') or 0,
                osu_score.get('user_id') or 0,
            ))
            
            return True
    except Exception as e:
        print('add_score error:',e)
        return False

def find_scores(
    *,
    version: int,
    mode: str,
    ranked: int,
    failed: int,
    sort_by: str = "pp",
    descending: bool = True,
    limit: int = 50,
) -> List[Dict[str, Any]]:

    if sort_by not in ALLOWED_SORTS:
        raise ValueError(f"Unsupported sort field: {sort_by}")

    column = ALLOWED_SORTS[sort_by]
    order = "DESC" if descending else "ASC"

    sql = f"""
    SELECT *
    FROM scores_state
    WHERE
        schema_version = ?
        AND mode = ?
        AND ranked_flag = ?
        AND fail_flag = ?
    ORDER BY {column} {order}
    LIMIT ?
    """

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            sql,
            (version, mode, ranked, failed, limit),
        )
        rows = cur.fetchall()

    return [dict(r) for r in rows]

def find_random_scores(
    *,
    version: int,
    mode: str,
    ranked: int,
    failed: int,
    ignore_ids: List[int] = None,
    sort_by: str = "pp",
    max_diff: float = None,
    limit: int = 10,
    sample_size: int = 1000
) -> List[Dict[str, Any]]:
    """
    Поиск случайных скорoв с фильтром по версии, ранкед/fail,
    игнорируя ignore_ids, ограничивая max_diff по sort_by
    """
    if sort_by not in ALLOWED_SORTS:
        raise ValueError(f"Unsupported sort field: {sort_by}")
    
    column = ALLOWED_SORTS[sort_by]
    ignore_ids = ignore_ids or []

    where_clauses = [
        "schema_version = ?",
        "mode = ?",
        "ranked_flag = ?",
        "fail_flag = ?"
    ]
    params = [version, mode, ranked, failed]

    if ignore_ids:
        placeholders = ",".join("?" for _ in ignore_ids)
        where_clauses.append(f"id NOT IN ({placeholders})")
        params.extend(ignore_ids)

    # max_diff
    pivot = None
    if max_diff is not None:
        pivot_sql = f"""
        SELECT {column} 
        FROM scores_state
        WHERE {' AND '.join(where_clauses)}
        ORDER BY RANDOM()
        LIMIT 1
        """
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(pivot_sql, params)
            row = cur.fetchone()
            if row is None:
                return []
            pivot = row[0]
        
        where_clauses.append(f"{column} BETWEEN ? AND ?")
        params.extend([pivot - max_diff, pivot + max_diff])

    # sample_size
    sql = f"""
    SELECT *
    FROM scores_state
    WHERE {' AND '.join(where_clauses)}
    ORDER BY {column} ASC
    LIMIT ?
    """
    params.append(sample_size)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        rows = cur.fetchall()

    rows_list = list(rows)
    if not rows_list:
        return []

    # random
    if len(rows_list) <= limit:
        selected = rows_list
    else:
        selected = random.sample(rows_list, limit)

    return [dict(r) for r in selected]



init_db()
