


import sqlite3



def search_beatmaps(db_path, mods=None, filters=None, limit=10, offset=0, order_by_total=True, lazer=True):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    where_clauses = []
    params = []

    if mods:
        placeholders = ",".join("?" for _ in mods)
        where_clauses.append(f"mod IN ({placeholders})")
        params.extend(mods)

    if filters:
        for stat, val in filters.items():
            if isinstance(val, tuple) and len(val) == 2 and all(isinstance(v, (int, float)) for v in val):
                
                where_clauses.append(f"{stat} BETWEEN ? AND ?")
                params.extend(val)
            elif isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], str):
                
                op, v = val
                where_clauses.append(f"{stat} {op} ?")
                params.append(v)

    where_clauses.append("mode = ?")
    params.append("lazer" if lazer else "stable")

    where_sql = " AND ".join(where_clauses)

    sql = f"""
        SELECT map_id, mode, mod, aim, speed, acc, (aim + speed + acc) AS total
        FROM beatmaps
        {f'WHERE {where_sql}' if where_sql else ''}
        {'ORDER BY total DESC' if order_by_total else ''}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    cur.execute(sql, params)
    results = cur.fetchall()
    conn.close()
    return results
