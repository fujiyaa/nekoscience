import math
import sqlite3
import time
import os
import json
import hmac
import hashlib
import urllib.parse
import asyncio
from typing import List, Set, Dict, Optional
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError
from collections import defaultdict

templates = Jinja2Templates(directory="templates")
router = APIRouter()

DB_NAME = "game_not_debug.db"
BOT_TOKEN = os.getenv("TOKEN")

SIZE = 100
CELL = 50
BLAST_RADIUS = 7
DRAW_COOLDOWN_SEC = 15
ERASE_COOLDOWN_SEC = 20
ERASE_COOLDOWN_PER_100_AREA = 5
BLAST_COOLDOWN_SEC = 10000
DRAW_MAX_CHARGES = 5

GAME_GRID_CACHE = []
last_action_times = {}
GAME_STATE_CACHE = {}

DIRS = [(1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1)]

class ActionPayload(BaseModel):
    player_id: int
    tool: str = Field(..., pattern="^(draw|erase|blast)$")
    x: int = Field(..., ge=0, lt=SIZE) # от 0 до SIZE-1
    y: int = Field(..., ge=0, lt=SIZE) # от 0 до SIZE-1

def validate_telegram_data(init_data: str) -> bool:
    parsed_data = urllib.parse.parse_qs(init_data)
    if 'hash' not in parsed_data:
        return False
    
    received_hash = parsed_data.pop('hash')[0]
    
    data_check_string = "\n".join([f"{k}={v[0]}" for k, v in sorted(parsed_data.items())])
    
    secret_key = hmac.new("WebAppData".encode(), BOT_TOKEN.encode(), hashlib.sha256).digest()
    
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    return hmac.compare_digest(calculated_hash, received_hash)

def load_grid_from_db(cursor) -> List[List[int]]:
    cursor.execute("SELECT x, y, contour_id FROM game_grid")
    grid = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
    for x, y, c_id in cursor.fetchall():
        grid[y][x] = c_id
    return grid

def migrate_db(cursor):
    cursor.execute("PRAGMA table_info(players)")
    columns = [row[1] for row in cursor.fetchall()]

    if "blast_cooldown_start" not in columns:
        cursor.execute("""
            ALTER TABLE players
            ADD COLUMN blast_cooldown_start REAL DEFAULT 0
        """)

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS game_grid (
                x INTEGER, y INTEGER, contour_id INTEGER DEFAULT 0, PRIMARY KEY (x, y)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY,
                username TEXT, -- Сохраняем имя при первом входе
                draw_charges INTEGER DEFAULT 5,
                draw_cooldown_start REAL DEFAULT 0,
                erase_cooldown_start REAL DEFAULT 0,
                blast_cooldown_start REAL DEFAULT 0
            )
        """)
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM game_grid")
        if cursor.fetchone()[0] == 0:
            grid_data = [(x, y, 0) for y in range(SIZE) for x in range(SIZE)]
            cursor.executemany("INSERT INTO game_grid (x, y, contour_id) VALUES (?, ?, ?)", grid_data)
            # for p_id in range(1, 5):
            #     cursor.execute("INSERT OR IGNORE INTO players (player_id) VALUES (?)", (p_id,))
            # conn.commit()

        global GAME_GRID_CACHE
        GAME_GRID_CACHE = load_grid_from_db(cursor)

        # migrate_db(cursor)
        # conn.commit()

async def background_cooldown_cleanup():
    while True:
        try:
            now = time.time()
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE players 
                    SET draw_charges = 5, draw_cooldown_start = 0 
                    WHERE draw_cooldown_start > 0 AND (draw_cooldown_start + 10) <= ?
                """, (now,))
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче очистки: {e}")
        
        await asyncio.sleep(10)

init_db()

def get_cells_in_radius(x: int, y: int, r: int):
    cells = []
    r2 = r * r
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny) and dx*dx + dy*dy <= r2:
                cells.append((nx, ny))
    return cells

def get_player_by_contour(contour_id: int) -> Optional[int]:
    if contour_id == 0:
        return None
    return contour_id // 10000

def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < SIZE and 0 <= y < SIZE

def update_cell_in_db(cursor, x: int, y: int, contour_id: int):
    cursor.execute("UPDATE game_grid SET contour_id = ? WHERE x = ? AND y = ?", (contour_id, x, y))

def sync_grid_to_db(cursor, new_grid: List[List[int]]):
    global GAME_GRID_CACHE
    
    for y in range(SIZE):
        for x in range(SIZE):
            if new_grid[y][x] != GAME_GRID_CACHE[y][x]:
                update_cell_in_db(cursor, x, y, new_grid[y][x])
                GAME_GRID_CACHE[y][x] = new_grid[y][x]


def get_free_contour_id(grid: List[List[int]], player_id: int) -> int:
    used = {cell for row in grid for cell in row if cell != 0}
    contour_id = player_id * 10000 + 1
    while contour_id in used:
        contour_id += 1
    return contour_id

def get_neighbour_contours(x: int, y: int, player_id: int, grid: List[List[int]]) -> List[int]:
    neighbours = set()
    for dx, dy in DIRS:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny):
            c_id = grid[ny][nx]
            if c_id != 0 and get_player_by_contour(c_id) == player_id:
                neighbours.add(c_id)
    return list(neighbours)

def recalculate_player_contours(player_id: int, grid: List[List[int]]):
    visited = [[False for _ in range(SIZE)] for _ in range(SIZE)]
    
    for y in range(SIZE):
        for x in range(SIZE):
            c_id = grid[y][x]
            if c_id != 0 and get_player_by_contour(c_id) == player_id and not visited[y][x]:
                
                new_contour_id = get_free_contour_id(grid, player_id)
                
                
                queue = [(x, y)]
                visited[y][x] = True
                grid[y][x] = new_contour_id
                
                while queue:
                    cx, cy = queue.pop(0)
                    for dx, dy in DIRS:
                        nx, ny = cx + dx, cy + dy
                        if in_bounds(nx, ny) and not visited[ny][nx]:
                            nc_id = grid[ny][nx]
                            if nc_id != 0 and get_player_by_contour(nc_id) == player_id:
                                visited[ny][nx] = True
                                grid[ny][nx] = new_contour_id
                                queue.append((nx, ny))

def build_mask(grid: List[List[int]], contour_id: int) -> List[List[int]]:
    return [[1 if grid[y][x] == contour_id else 0 for x in range(SIZE)] for y in range(SIZE)]

def trace_contour(mask: List[List[int]]) -> List[Dict[str, int]]:
    points = []
    point_map = {}
    
    for y in range(SIZE):
        for x in range(SIZE):
            if mask[y][x] == 1:
                p = {"x": x, "y": y, "neighbors": []}
                points.append(p)
                point_map[f"{x},{y}"] = p

    if not points: return []
    if len(points) == 1: return [{"x": points[0]["x"], "y": points[0]["y"]}]

    
    for i, p1 in enumerate(points):
        for j, p2 in enumerate(points):
            if i == j: continue
            dx, dy = p2["x"] - p1["x"], p2["y"] - p1["y"]
            if dx*dx + dy*dy <= 2:
                p1["neighbors"].append(p2)

    
    for p in points:
        p["neighbors"].sort(key=lambda n: math.atan2(n["y"] - p["y"], n["x"] - p["x"]))

    
    start = points[0]
    for p in points:
        if p["y"] < start["y"] or (p["y"] == start["y"] and p["x"] < start["x"]):
            start = p

    contour = []
    current = start
    prev_x, prev_y = start["x"] - 1, start["y"]
    visited_edges = set()
    max_steps = len(points) * 4
    steps = 0

    while steps < max_steps:
        contour.append({"x": current["x"], "y": current["y"]})
        if not current["neighbors"]: break

        base_angle = math.atan2(prev_y - current["y"], prev_x - current["x"])
        next_node = None
        min_diff = float('inf')

        for neighbor in current["neighbors"]:
            angle = math.atan2(neighbor["y"] - current["y"], neighbor["x"] - current["x"])
            diff = angle - base_angle
            if diff <= 0: diff += math.pi * 2
            if diff < min_diff:
                min_diff = diff
                next_node = neighbor

        if not next_node: break

        edge_key = f"{current['x']},{current['y']}->{next_node['x']},{next_node['y']}"
        if edge_key in visited_edges:
            if next_node == start:
                contour.append({"x": start["x"], "y": start["y"]})
            break
        visited_edges.add(edge_key)

        prev_x, prev_y = current["x"], current["y"]
        current = next_node
        steps += 1

    if contour and current == start:
        contour.append({"x": start["x"], "y": start["y"]})
        
    return contour

def calculate_contour_area(points: List[Dict[str, int]]) -> float:
    if len(points) < 3: return 0.0
    area = 0.0
    j = len(points) - 1
    for i in range(len(points)):
        prev = points[j if i == 0 else i - 1]
        curr = points[i]
        area += (prev["x"] + curr["x"]) * (prev["y"] - curr["y"])
    return abs(area / 2.0)

def calculate_player_total_area(grid: List[List[int]], player_id: int) -> float:    
    total_area = 0.0
    unique_ids = {cell for row in grid for cell in row if cell != 0}
    
    for c_id in unique_ids:
        if get_player_by_contour(c_id) == player_id:
            mask = build_mask(grid, c_id)
            path = trace_contour(mask)
            total_area += calculate_contour_area(path)
            
    return total_area

def get_cooldown_progress(cooldown_start: float, duration: float, now: float) -> float:
    if cooldown_start == 0: return 0
    elapsed = now - cooldown_start
    return max(0, duration - elapsed)

def get_player_stats(cursor, now: float, player_areas: Dict[int, float]) -> Dict[int, dict]:
    cursor.execute("SELECT player_id, draw_charges, draw_cooldown_start, erase_cooldown_start, blast_cooldown_start FROM players")
    stats = {}
    
    for p_id, charges, d_start, e_start, b_start in cursor.fetchall():
        # +5 сек за каждые 100 площади, минимум ERASE_COOLDOWN_SEC
        area = player_areas.get(p_id, 0.0)
        erase_duration = (
            ERASE_COOLDOWN_SEC
            + (int(area) // 100) * ERASE_COOLDOWN_PER_100_AREA
        )
        
        is_draw_ready = (d_start > 0 and (now - d_start) >= DRAW_COOLDOWN_SEC)
        
        d_rem = max(0, int((d_start + DRAW_COOLDOWN_SEC - now) * 1000)) if (d_start > 0 and not is_draw_ready) else 0
        e_rem = max(0, int((e_start + erase_duration - now) * 1000)) if e_start > 0 else 0
        b_rem = max(0, int((b_start + BLAST_COOLDOWN_SEC - now) * 1000)) if b_start > 0 else 0
        
        stats[p_id] = {
            "cooldowns": {
                "draw": {"charges": charges, "maxCharges": DRAW_MAX_CHARGES, "current": d_rem, "max": DRAW_COOLDOWN_SEC * 1000},
                "erase": {"current": e_rem, "max": erase_duration * 1000},
                "blast": {"current": b_rem, "max": BLAST_COOLDOWN_SEC * 1000}
            }
        }
    return stats

def get_current_state_dict():
    global GAME_STATE_CACHE

    if not GAME_STATE_CACHE:
        refresh_game_state_cache()
    return GAME_STATE_CACHE

def refresh_game_state_cache():
    global GAME_STATE_CACHE

    now = time.time()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        grid = load_grid_from_db(cursor)
        unique_ids = {cell for row in grid for cell in row if cell != 0}
        
        serialized_contours = []
        player_areas = defaultdict(float)
        
        for c_id in unique_ids:
            mask = build_mask(grid, c_id)
            path = trace_contour(mask)
            area = calculate_contour_area(path)
            p_id = get_player_by_contour(c_id)
            if p_id is not None:
                player_areas[p_id] += area
            serialized_contours.append({"id": c_id, "player_id": p_id, "path": path})
        
        cursor.execute("SELECT player_id, username FROM players")
        leaderboard = []
        for p_id, name in cursor.fetchall():
            leaderboard.append({
                "player_id": p_id, 
                "name": name, 
                "totalArea": player_areas.get(p_id, 0.0)
            })
        leaderboard.sort(key=lambda x: x["totalArea"], reverse=True)

        players_data = get_player_stats(cursor, now, player_areas)
        
    GAME_STATE_CACHE = {
        "config": {"size": SIZE, "cell": CELL},
        "grid": grid, 
        "contours": serialized_contours, 
        "leaderboard": leaderboard,
        "players": players_data
    }



class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try: await connection.send_json(message)
            except Exception: pass

manager = ConnectionManager()

@router.get("/game", response_class=HTMLResponse)
async def game(request: Request):
    return templates.TemplateResponse("game.html", {"request": request})

import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("game_ws")
logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler("game.log", maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

@router.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Удалена отправка init здесь: теперь ждем auth
    logger.info("WS: Установлено новое сырое соединение")

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            # 1. Heartbeat
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            # 2. Authorization
            if msg_type == "auth":
                init_data = data.get("initData")
                if not init_data or not validate_telegram_data(init_data):
                    logger.warning("WS: Провал авторизации")
                    await websocket.send_json({"type": "error", "message": "Invalid Authorization"})
                    await websocket.close(code=1008)
                    return

                user_info = json.loads(urllib.parse.parse_qs(init_data)['user'][0])
                p_id = user_info['id']
                
                for conn in manager.active_connections:
                    if getattr(conn, "player_id", None) == p_id and conn != websocket:
                        try:
                            await conn.close()
                        except:
                            pass
                
                websocket.player_id = p_id
                
                with sqlite3.connect(DB_NAME, timeout=5) as conn:
                    conn.execute("PRAGMA journal_mode=WAL;") # Убедитесь, что это есть
                    conn.execute("""
                        INSERT INTO players (player_id, username) VALUES (?, ?)
                        ON CONFLICT(player_id) DO UPDATE SET username=excluded.username
                    """, (p_id, user_info.get('first_name', 'Player')))
                
                await websocket.send_json({"type": "auth_success", "player_id": p_id})
                
                await asyncio.sleep(0.2) 
                
                state = get_current_state_dict()
                await websocket.send_json({"type": "init", "data": state})
                
                logger.info(f"WS: Игрок {p_id} успешно авторизован и получил стейт")
                continue

            # 3. Game Actions
            if msg_type == "action":
                player_id = getattr(websocket, "player_id", None)
                if not player_id:
                    continue

                if time.time() - last_action_times.get(player_id, 0) < 0.2:
                    continue
                last_action_times[player_id] = time.time()

                try:
                    payload = ActionPayload(**data["payload"]).model_dump()
                    tool, x, y = payload["tool"], int(payload["x"]), int(payload["y"])
                    
                    if not in_bounds(x, y): continue

                    with sqlite3.connect(DB_NAME) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT draw_charges, draw_cooldown_start, erase_cooldown_start, blast_cooldown_start FROM players WHERE player_id = ?", (player_id,))
                        row = cursor.fetchone()
                        if not row: continue
                        
                        charges, d_start, e_start, b_start = row
                        grid = load_grid_from_db(cursor)
                        action_valid = False
                        now = time.time()

                        # --- ЛОГИКА ДЕЙСТВИЙ (Draw, Erase, Blast) ---
                        if tool == "draw" and grid[y][x] == 0:
                            if charges > 0 or (d_start + DRAW_COOLDOWN_SEC) <= now:
                                action_valid = True
                                neighbours = get_neighbour_contours(x, y, player_id, grid)
                                grid[y][x] = neighbours[0] if len(neighbours) == 1 else (get_free_contour_id(grid, player_id) if not neighbours else None)
                                if len(neighbours) > 1: # Объединение
                                    main_id = neighbours[0]
                                    for yy in range(SIZE):
                                        for xx in range(SIZE):
                                            if grid[yy][xx] in neighbours: grid[yy][xx] = main_id
                                    grid[y][x] = main_id
                                new_charges = charges - 1 if charges > 0 else 4
                                cursor.execute("UPDATE players SET draw_charges = ?, draw_cooldown_start = ? WHERE player_id = ?", (new_charges, now if new_charges == 0 else 0, player_id))

                        elif tool == "erase" and grid[y][x] != 0:
                            player_area = calculate_player_total_area(grid, player_id)

                            erase_duration = (
                                ERASE_COOLDOWN_SEC
                                + (int(player_area) // 100) * ERASE_COOLDOWN_PER_100_AREA
                            )

                            if (e_start + erase_duration) <= now:
                                action_valid = True
                                target_pid = get_player_by_contour(grid[y][x])
                                grid[y][x] = 0
                                if target_pid: recalculate_player_contours(target_pid, grid)
                                cursor.execute("UPDATE players SET erase_cooldown_start = ? WHERE player_id = ?", (now, player_id))

                        elif tool == "blast" and (b_start + BLAST_COOLDOWN_SEC) <= now:
                            action_valid = True
                            affected = {get_player_by_contour(grid[ny][nx]) for nx, ny in get_cells_in_radius(x, y, BLAST_RADIUS) if grid[ny][nx] != 0}
                            for nx, ny in get_cells_in_radius(x, y, BLAST_RADIUS): grid[ny][nx] = 0
                            for pid in [p for p in affected if p]: recalculate_player_contours(pid, grid)
                            cursor.execute("UPDATE players SET blast_cooldown_start = ? WHERE player_id = ?", (now, player_id))

                        if action_valid:
                            sync_grid_to_db(cursor, grid)
                            conn.commit()

                    refresh_game_state_cache()

                    updated_state = get_current_state_dict()

                    await manager.broadcast({"type": "update", "data": updated_state})
                except Exception as e:
                    logger.error(f"WS: Ошибка обработки действия: {e}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WS: Отключен (игрок {getattr(websocket, 'player_id', 'Unknown')})")
    except Exception as e:
        logger.exception(f"WS: Критическая ошибка: {e}")


@router.on_event("startup")
async def startup_event():
    asyncio.create_task(background_cooldown_cleanup())