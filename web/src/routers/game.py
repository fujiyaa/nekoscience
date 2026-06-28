import math
import sqlite3
import time
import os
import json, re
import hmac
import hashlib
import urllib.parse
import asyncio
import traceback
from typing import List, Set, Dict, Optional, Callable
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError
from collections import defaultdict, deque
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass

templates = Jinja2Templates(directory="templates")
router = APIRouter()

DB_NAME = "game_v2.db"
BOT_TOKEN = os.getenv("TOKEN")

SIZE = 200
CELL = 50

GAME_GRID_CACHE = []
last_action_times = {}
GAME_STATE_CACHE = {}
CONTOUR_PATHS_CACHE = {}

DIRS = [(1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1)]



@dataclass
class ToolConfig:
    name: str
    base_cooldown_sec: float
    max_charges: Optional[int] = None
    area_scaling: Optional[Callable[[float], float]] = None
    radius: Optional[int] = None

    def cooldown_ms(self, area: float = 0) -> int:
        base = self.base_cooldown_sec * 1000
        if self.area_scaling:
            base += int(self.area_scaling(area))
        return int(base)
    
class ActionPayload(BaseModel):
    player_id: int
    tool: str = Field(..., pattern="^(draw|erase|blast|sign|structure|tier2draw|tier2erase|tier2blast)$")
    x: int = Field(..., ge=0, lt=SIZE)
    y: int = Field(..., ge=0, lt=SIZE)
    text: Optional[str] = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        tasks = [
            asyncio.create_task(connection.send_json(message))
            for connection in self.active_connections
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

TOOLS = {
    "sign": ToolConfig(
        name="sign",
        base_cooldown_sec=1,
        max_charges=5,
    ),
    "structure": ToolConfig(
        name="structure",
        base_cooldown_sec=1,
        max_charges=5,
        radius=5,
    ),
    
    "draw": ToolConfig(
        name="draw",
        base_cooldown_sec=1,
        max_charges=5,
    ),
    "erase": ToolConfig(
        name="erase",
        base_cooldown_sec=3,
        max_charges=3,
        area_scaling=lambda area: (area // 100) * 3000,
    ),
    "blast": ToolConfig(
        name="blast",
        base_cooldown_sec=1,
        max_charges=1,
        radius=14,
    ),

    "tier2draw": ToolConfig(
        name="tier2draw",
        base_cooldown_sec=1,
        max_charges=5,
    ),
    "tier2erase": ToolConfig(
        name="tier2erase",
        base_cooldown_sec=3,
        max_charges=3,
        area_scaling=lambda area: (area // 100) * 3000,
    ),
    "tier2blast": ToolConfig(
        name="tier2blast",
        base_cooldown_sec=1,
        max_charges=1,
        radius=6,
    ),
}

manager = ConnectionManager()

logger = logging.getLogger("game_ws")
logger.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler("game.log", maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


def load_external_passwords():
    path = os.path.join(os.path.dirname(DB_NAME), "miniapp_passwords.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Не удалось прочитать external passwords: {e}")
        return {}

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

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS cells (
                x INTEGER, y INTEGER, 
                player_id INTEGER, 
                contour_id INTEGER, 
                PRIMARY KEY (x, y)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cell_types (
                x INTEGER, y INTEGER, 
                type_id TEXT,       -- 'Dot', 'Sign', и т.д.
                type_data TEXT,     -- JSON с данными
                PRIMARY KEY (x, y),
                FOREIGN KEY (x, y) REFERENCES cells(x, y) ON DELETE CASCADE
            )
        """)

        tool_columns = []

        for key, cfg in TOOLS.items():
            if cfg.max_charges is not None:
                tool_columns.append(
                    f"{key}_charges INTEGER DEFAULT {cfg.max_charges}"
                )

            tool_columns.append(
                f"{key}_cooldown_start REAL DEFAULT 0"
            )

        tool_columns_sql = ",\n                ".join(tool_columns)
        
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY,
                username TEXT,

                {tool_columns_sql}
            )
        """)

        conn.commit()

        cursor.execute("PRAGMA table_info(players)")
        existing = {row[1] for row in cursor.fetchall()}

        for key, cfg in TOOLS.items():
            charge_col = f"{key}_charges"
            cooldown_col = f"{key}_cooldown_start"

            if cfg.max_charges is not None and charge_col not in existing:
                cursor.execute(
                    f"ALTER TABLE players ADD COLUMN {charge_col} "
                    f"INTEGER DEFAULT {cfg.max_charges}"
                )

            if cooldown_col not in existing:
                cursor.execute(
                    f"ALTER TABLE players ADD COLUMN {cooldown_col} "
                    "REAL DEFAULT 0"
                )
                
        conn.commit()

        global GAME_GRID_CACHE
        GAME_GRID_CACHE = load_grid_from_db(cursor)

def update_cell_ownership(cursor, x: int, y: int, player_id: Optional[int], contour_id: int):
    if player_id is None:
        cursor.execute("DELETE FROM cells WHERE x = ? AND y = ?", (x, y))
    else:
        cursor.execute("""
            INSERT INTO cells (x, y, player_id, contour_id) VALUES (?, ?, ?, ?)
            ON CONFLICT(x, y) DO UPDATE SET player_id=excluded.player_id, contour_id=excluded.contour_id
        """, (x, y, player_id, contour_id))

def set_cell_type(cursor, x: int, y: int, type_id: str, data: Optional[dict] = None):
    if type_id is None:
        cursor.execute("DELETE FROM cell_types WHERE x = ? AND y = ?", (x, y))
    else:
        cursor.execute("""
            INSERT INTO cell_types (x, y, type_id, type_data) VALUES (?, ?, ?, ?)
            ON CONFLICT(x, y) DO UPDATE SET type_id=excluded.type_id, type_data=excluded.type_data
        """, (x, y, type_id, json.dumps(data) if data else None))

def get_cell_info(cursor, x: int, y: int):
    cursor.execute("""
        SELECT c.player_id, c.contour_id, t.type_id, t.type_data 
        FROM cells c 
        LEFT JOIN cell_types t ON c.x = t.x AND c.y = t.y
        WHERE c.x = ? AND c.y = ?
    """, (x, y))
    row = cursor.fetchone()
    if not row: return None
    return {
        "player_id": row[0],
        "contour_id": row[1],
        "type": {"id": row[2], "data": json.loads(row[3]) if row[3] else None}
    }

def load_grid_from_db(cursor) -> List[List[dict]]:
    grid = [[{"player_id": None, "contour_id": 0, "type": None} for _ in range(SIZE)] for _ in range(SIZE)]
    
    cursor.execute("""
        SELECT c.x, c.y, c.player_id, c.contour_id, t.type_id, t.type_data 
        FROM cells c 
        LEFT JOIN cell_types t ON c.x = t.x AND c.y = t.y
    """)
    
    for x, y, p_id, c_id, t_id, t_data in cursor.fetchall():
        grid[y][x] = {
            "player_id": p_id,
            "contour_id": c_id,
            "type": {"id": t_id, "data": json.loads(t_data) if t_data else None} if t_id else None
        }
    return grid

def update_cache_cell(x, y, new_data: dict):
    global GAME_GRID_CACHE
    GAME_GRID_CACHE[y][x].update(new_data)

def sync_grid_to_db(cursor, new_grid: List[List[dict]]):
    global GAME_GRID_CACHE
    
    for y in range(SIZE):
        for x in range(SIZE):
            new_cell = new_grid[y][x]
            old_cell = GAME_GRID_CACHE[y][x]
            
            if (new_cell["player_id"] != old_cell["player_id"] or 
                new_cell["contour_id"] != old_cell["contour_id"]):
                
                update_cell_ownership(
                    cursor, x, y, 
                    new_cell["player_id"], 
                    new_cell["contour_id"]
                )
                GAME_GRID_CACHE[y][x]["player_id"] = new_cell["player_id"]
                GAME_GRID_CACHE[y][x]["contour_id"] = new_cell["contour_id"]

            if new_cell["type"] != old_cell["type"]:
                set_cell_type(
                    cursor,
                    x,
                    y,
                    new_cell["type"]["id"] if new_cell["type"] else None,
                    new_cell["type"]["data"] if new_cell["type"] else None,
                )

                GAME_GRID_CACHE[y][x]["type"] = new_cell["type"]

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

def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < SIZE and 0 <= y < SIZE

def get_free_contour_id(grid: List[List[dict]], player_id: int) -> int:
    used_ids = {
        cell["contour_id"] 
        for row in grid 
        for cell in row 
        if cell["player_id"] == player_id and cell["contour_id"] != 0
    }
    
    contour_id = 1
    while contour_id in used_ids:
        contour_id += 1
        
    return contour_id

def get_neighbour_contours(x: int, y: int, player_id: int, grid: List[List[dict]]) -> List[int]:
    neighbours = set()
    for dx, dy in DIRS:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny):
            cell = grid[ny][nx]
            if cell["player_id"] == player_id and cell["contour_id"] != 0:
                neighbours.add(cell["contour_id"])
    return list(neighbours)

def recalculate_player_contours_nearby(target_contour_id: int, player_id: int, grid: List[List[dict]]) -> Set[int]:
    cells_to_process = []
    
    for y in range(SIZE):
        for x in range(SIZE):
            cell = grid[y][x]
            if cell["player_id"] == player_id and cell["contour_id"] == target_contour_id:
                cells_to_process.append((x, y))
                grid[y][x]["contour_id"] = 0  # временно

    if not cells_to_process:
        return set()

    new_ids = set()
    cells_set = set(cells_to_process)
    visited = set()
    
    for x, y in cells_to_process:
        if (x, y) not in visited:
            new_id = get_free_contour_id(grid, player_id)
            new_ids.add(new_id)            
            queue = deque([(x, y)])
            visited.add((x, y))
            grid[y][x]["contour_id"] = new_id            
            while queue:
                cx, cy = queue.popleft()
                for dx, dy in DIRS:
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) in cells_set and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        grid[ny][nx]["contour_id"] = new_id
                        queue.append((nx, ny))
                        
    return new_ids

def recalculate_player_contours(player_id: int, grid: List[List[dict]]):
    visited = [[False for _ in range(SIZE)] for _ in range(SIZE)]
    
    for y in range(SIZE):
        for x in range(SIZE):
            cell = grid[y][x]
            if cell["player_id"] == player_id and cell["contour_id"] != 0 and not visited[y][x]:                
                new_contour_id = get_free_contour_id(grid, player_id)                
                queue = [(x, y)]
                visited[y][x] = True
                grid[y][x]["contour_id"] = new_contour_id                
                while queue:
                    cx, cy = queue.pop(0)
                    for dx, dy in DIRS:
                        nx, ny = cx + dx, cy + dy
                        if in_bounds(nx, ny) and not visited[ny][nx]:
                            neighbor_cell = grid[ny][nx]
                            if neighbor_cell["player_id"] == player_id and neighbor_cell["contour_id"] != 0:
                                visited[ny][nx] = True
                                grid[ny][nx]["contour_id"] = new_contour_id
                                queue.append((nx, ny))

def build_mask(grid: List[List[dict]], contour_id: int) -> List[List[int]]:
    return [
        [1 if grid[y][x]["contour_id"] == contour_id else 0 for x in range(SIZE)] 
        for y in range(SIZE)
    ]

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

def calculate_player_total_area(grid: List[List[dict]], player_id: int) -> float:    
    total_area = 0.0
    unique_ids = {
        cell["contour_id"] 
        for row in grid 
        for cell in row 
        if cell["player_id"] == player_id and cell["contour_id"] != 0
    }
    
    for c_id in unique_ids:
        # build_mask теперь принимает grid в новом формате
        mask = build_mask(grid, c_id)
        path = trace_contour(mask)
        total_area += calculate_contour_area(path)
            
    return total_area

def get_player_stats(cursor, player_areas, player_id=None, tools=None):
    query = build_query(player_id, tools)

    if player_id is not None:
        cursor.execute(query, (player_id,))
        rows = [cursor.fetchone()]
    else:
        cursor.execute(query)
        rows = cursor.fetchall()

    stats = {}

    for row in rows:
        if not row:
            continue

        idx = 0
        p_id = row[idx]
        idx += 1

        area = player_areas.get(p_id, 0.0)

        cooldowns = {}

        for key, cfg in TOOLS.items():
            if tools and key not in tools:
                continue

            charge = None
            if cfg.max_charges is not None:
                charge = row[idx]
                idx += 1

            start = row[idx]
            idx += 1

            duration = cfg.cooldown_ms(area)
            ends_at = (start + duration) if start else 0

            entry = {
                "endsAt": int(ends_at),
                "duration": duration,
            }

            if cfg.max_charges is not None:
                entry["charges"] = charge
                entry["maxCharges"] = cfg.max_charges

            cooldowns[key] = entry

        stats[p_id] = {"cooldowns": cooldowns}

    return stats

def build_query(player_id=None, tools=None):
    base_cols = ["player_id"]

    for key in TOOLS:
        if tools and key not in tools:
            continue

        cfg = TOOLS[key]

        if cfg.max_charges is not None:
            base_cols.append(f"{key}_charges")

        base_cols.append(f"{key}_cooldown_start")

    query = f"SELECT {', '.join(base_cols)} FROM players"

    if player_id is not None:
        query += " WHERE player_id = ?"

    return query

def refresh_contour_cache(grid: List[List[dict]], ids_to_update: Optional[Set[int]] = None):
    global CONTOUR_PATHS_CACHE
    
    if ids_to_update is not None:
        for c_id in ids_to_update:
            found = False
            for y in range(SIZE):
                for x in range(SIZE):
                    if grid[y][x]["contour_id"] == c_id:
                        found = True
                        break
                if found: break
            
            if found:
                mask = build_mask(grid, c_id)
                CONTOUR_PATHS_CACHE[c_id] = trace_contour(mask)
            elif c_id in CONTOUR_PATHS_CACHE:
                del CONTOUR_PATHS_CACHE[c_id]
    
    else:
        CONTOUR_PATHS_CACHE.clear()
        unique_ids = {cell["contour_id"] for row in grid for cell in row if cell["contour_id"] != 0}
        for c_id in unique_ids:
            mask = build_mask(grid, c_id)
            CONTOUR_PATHS_CACHE[c_id] = trace_contour(mask)

def get_current_state_dict():
    global GAME_STATE_CACHE

    if not GAME_STATE_CACHE:
        refresh_game_state_cache()
    return GAME_STATE_CACHE



def refresh_game_state_cache(updated_contour_ids: Optional[Set[int]] = None):
    global GAME_STATE_CACHE

    now = time.time()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        grid = load_grid_from_db(cursor)
        
        refresh_contour_cache(grid, updated_contour_ids)
        
        contour_to_player = {}
        for row in grid:
            for cell in row:
                c_id = cell["contour_id"]
                if c_id != 0 and c_id not in contour_to_player:
                    contour_to_player[c_id] = cell["player_id"]
        
        serialized_contours = []
        player_areas = defaultdict(float)
        
        for c_id, path in CONTOUR_PATHS_CACHE.items():
            p_id = contour_to_player.get(c_id)
            area = calculate_contour_area(path)
            
            if p_id is not None:
                player_areas[p_id] += area
            
            serialized_contours.append({
                "id": c_id, 
                "player_id": p_id, 
                "path": path
            })
        
        cursor.execute("SELECT player_id, username FROM players")
        leaderboard = [
            {
                "player_id": p_id, 
                "name": name, 
                "totalArea": player_areas.get(p_id, 0.0)
            }
            for p_id, name in cursor.fetchall()
        ]
        leaderboard.sort(key=lambda x: x["totalArea"], reverse=True)

        players_data = get_player_stats(cursor, player_areas)
        
    GAME_STATE_CACHE = {
        "config": {"size": SIZE, "cell": CELL},
        "grid": grid, 
        "contours": serialized_contours, 
        "leaderboard": leaderboard,
        "players": players_data
    }

@router.get("/game", response_class=HTMLResponse)
async def game(request: Request):
    return templates.TemplateResponse("game.html", {"request": request})

@router.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info("WS: Установлено новое сырое соединение")

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "auth":
                init_data = data.get("initData")
                if not init_data or not validate_telegram_data(init_data):
                    await websocket.send_json({"type": "error", "message": "Invalid Authorization"})
                    await websocket.close(code=1008)
                    return

                user_info = json.loads(urllib.parse.parse_qs(init_data)['user'][0])
                await perform_player_auth(websocket, user_info['id'], user_info.get('first_name', 'Player'))
                continue

            if msg_type == "external_auth":
                token = data.get("token")
                passwords = load_external_passwords()
                
                match = next(((int(tid), info) for tid, info in passwords.items() if info.get("code") == token), None)
                
                if not match:
                    await websocket.send_json({"type": "error", "message": "Wrong password"})
                    continue
                    
                await perform_player_auth(websocket, match[0], match[1].get("name", "Player"))
                continue

            # 3. Game Actions
            if msg_type == "action":
                action_valid = False
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

                    logger.info(f"WS: Action {tool} от {player_id} в ({x}, {y})")
                    
                    ids_to_refresh = set()
                    events = []

                    with sqlite3.connect(DB_NAME) as conn:
                        cursor = conn.cursor()
                        
                        grid = load_grid_from_db(cursor)
                        player_area = calculate_player_total_area(grid, player_id)

                        stats = get_player_stats(
                            cursor,
                            {player_id: player_area},
                            player_id=player_id,
                            tools=[
                                "draw", 
                                "erase", 
                                "blast", 
                                "sign",
                                "structure",
                                "tier2draw", 
                                "tier2erase", 
                                "tier2blast"
                            ]
                        )

                        tool_state = stats[player_id]["cooldowns"]                        
                        now = int(time.time() * 1000)

                        # --- SIGN ---
                        if tool == "sign":
                            raw_text = data["payload"].get("text", "")
                            text = sanitize_sign_text(raw_text)
                            
                            if not text or len(text) > 30:
                                continue

                            if not (0 <= y < len(grid) and 0 <= x < len(grid[0])):
                                continue
                                
                            if grid[y][x].get("type") is not None:
                                continue

                            if use_tool(cursor, player_id, "sign", tool_state["sign"], 0, now):
                                action_valid = True
                                events.append({"type": "sign_placed", "data": {"x": x, "y": y, "text": text}})

                                grid[y][x]["player_id"] = 0
                                grid[y][x]["contour_id"] = -1
                                grid[y][x]["type"] = {
                                    "id": "Sign",
                                    "data": {"text": text}
                                }

                                ids_to_refresh = [(x, y)] 

                                logger.info(f"WS: Sign placed by {player_id} at ({x},{y}) with text: {text}")
                                                
                        # --- DRAW ---
                        elif tool in ["draw", "tier2draw"] and grid[y][x]["contour_id"] == 0:
                            
                            cell_type_id = "Dot" if tool == "draw" else "T2Dot"

                            if use_tool(
                                cursor,
                                player_id,
                                tool,
                                tool_state[tool],
                                0,
                                now
                            ):
                                action_valid = True

                                neighbours = get_neighbour_contours(x, y, player_id, grid)

                                if len(neighbours) > 1:
                                    main_id = neighbours[0]
                                    ids_to_refresh.update(neighbours)

                                    for yy in range(SIZE):
                                        for xx in range(SIZE):
                                            if grid[yy][xx]["contour_id"] in neighbours:
                                                grid[yy][xx]["contour_id"] = main_id

                                    grid[y][x]["contour_id"] = main_id

                                else:
                                    new_id = neighbours[0] if neighbours else get_free_contour_id(grid, player_id)
                                    grid[y][x]["contour_id"] = new_id
                                    ids_to_refresh.add(new_id)

                                grid[y][x]["player_id"] = player_id
                                grid[y][x]["type"] = {"id": cell_type_id, "data": None}

                                events.append({
                                    "type": "dot_placed", 
                                    "data": {"x": x, "y": y, "type": cell_type_id}
                                })

                                logger.info(f"WS: Draw успешен, игрок {player_id}")
                       
                        # --- STRUCTURE ---
                        elif tool == "structure" and grid[y][x]["contour_id"] == 0:                                
                            cfg = TOOLS[tool]
                            radius = cfg.radius
                            radius_expand = cfg.radius
                                                            
                            check_radius = radius + radius_expand
                            is_clear = True
                            for nx, ny in get_cells_in_radius(x, y, check_radius):
                                if 0 <= nx < SIZE and 0 <= ny < SIZE:
                                    if grid[ny][nx]["contour_id"] != 0:
                                        is_clear = False
                                        break

                            if is_clear:
                                if use_tool(cursor, player_id, tool, tool_state[tool], 0, now): 
                                    action_valid = True                               
                                
                                    new_id = get_free_contour_id(grid, player_id)
                                                                       
                                    for nx in range(x - radius, x + radius + radius_expand):
                                        for ny in range(y - radius, y + radius + radius_expand):
                                            if 0 <= nx < SIZE and 0 <= ny < SIZE:
                                                if abs(nx - x) + abs(ny - y) == radius:
                                                    grid[ny][nx]["contour_id"] = new_id
                                                    grid[ny][nx]["player_id"] = player_id
                                                    grid[ny][nx]["type"] = {"id": "T2Dot", "data": None}
                                    
                                    ids_to_refresh.add(new_id)
                                    
                                    events.append({
                                        "type": "structure_placed",
                                        "data": {"x": x, "y": y, "radius": radius, "contour_id": new_id}
                                    })
                                    
                                    logger.info(f"WS: Structure успешно создан, игрок {player_id}")
                                                          
                            else:
                                events.append({
                                    "alert": "Структуре недостаточно места"
                                })

                        # --- ERASE / TIER2ERASE ---
                        elif tool in ["erase", "tier2erase"] and grid[y][x]["contour_id"] != 0:

                            cell = grid[y][x]
                            cell_type = cell.get("type", {}).get("id")

                            if cell_type == "Stone":
                                continue

                            if tool == "erase" and cell_type in ["T2Dot", "Sign"]:
                                continue

                            if use_tool(cursor, player_id, tool, tool_state[tool], player_area, now):
                                action_valid = True
                                
                                target_contour_id = grid[y][x]["contour_id"]
                                target_pid = grid[y][x]["player_id"]
                                
                                grid[y][x]["contour_id"] = 0
                                grid[y][x]["player_id"] = None
                                grid[y][x]["type"] = None

                                if target_pid:
                                    new_contour_ids = recalculate_player_contours_nearby(
                                        target_contour_id, target_pid, grid
                                    )
                                    ids_to_refresh.add(target_contour_id)
                                    ids_to_refresh.update(new_contour_ids)

                                event_data = {"type": "dot_erased", "data": {"x": x, "y": y}}
                                events.append(event_data)

                                logger.info(f"WS: {tool} успешно завершен для {player_id}")                            
                                
                        # --- BLAST / TIER2BLAST---
                        elif tool in ["blast", "tier2blast"] and grid[y][x]["contour_id"] != 0:

                            if use_tool(
                                cursor,
                                player_id,
                                tool,
                                tool_state[tool],
                                0,
                                now
                            ):
                                action_valid = True

                                cfg = TOOLS[tool]
                                radius = cfg.radius

                                immune_types = ["Stone"]
                                if tool == "blast":
                                    immune_types.extend(["T2Dot", "Sign"])

                                affected_pids = {
                                    grid[ny][nx]["player_id"]
                                    for nx, ny in get_cells_in_radius(x, y, radius)
                                    if (
                                        grid[ny][nx]["contour_id"] != 0 
                                        and (grid[ny][nx].get("type") or {}).get("id") not in immune_types
                                    )
                                }

                                for nx, ny in get_cells_in_radius(x, y, radius):
                                    cell = grid[ny][nx]
                                    cell_type = (cell.get("type") or {}).get("id")

                                    if cell_type in immune_types:
                                        continue

                                    cell["contour_id"] = 0
                                    cell["player_id"] = None
                                    cell["type"] = None

                                for pid in [p for p in affected_pids if p]:
                                    recalculate_player_contours(pid, grid)

                                ids_to_refresh = None

                                events.append({
                                        "type": "explosion", 
                                        "data": {"x": x, "y": y, "radius": radius, "player_id": player_id}
                                    })

                                logger.info(f"WS: Blast успешен, игрок {player_id}")

                        if action_valid:
                            sync_grid_to_db(cursor, grid)
                            conn.commit()
                            logger.debug("WS: Данные успешно записаны в БД")

                    refresh_game_state_cache(updated_contour_ids=ids_to_refresh)
                    message = {
                        "type": "update", 
                        "data": get_current_state_dict(),
                        "events": events
                    }
                    
                    await manager.broadcast(message)
                    logger.info("WS: Стейт обновлен и разослан клиентам")
                        
                except Exception as e:
                    logger.error(f"WS: Ошибка обработки действия: {e}\n{traceback.format_exc()}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WS: Отключен (игрок {getattr(websocket, 'player_id', 'Unknown')})")
    except Exception as e:
        logger.error(f"WS: Ошибка: {e}\n{traceback.format_exc()}")

async def perform_player_auth(websocket, p_id: int, username: str):    
    for conn in manager.active_connections:
        if getattr(conn, "player_id", None) == p_id and conn != websocket:
            try:
                await conn.send_json({"type": "session_replaced"})
                await asyncio.sleep(0.1)
                await conn.close()
            except Exception as e:
                logger.error(f"Ошибка закрытия старой сессии: {e}")
    
    websocket.player_id = p_id
    
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            INSERT INTO players (player_id, username) VALUES (?, ?)
            ON CONFLICT(player_id) DO UPDATE SET username=excluded.username
        """, (p_id, username))
    
    await websocket.send_json({"type": "auth_success", "player_id": p_id})
    await asyncio.sleep(0.2)
    
    state = get_current_state_dict()
    await websocket.send_json({"type": "init", "data": state})
    logger.info(f"WS: Игрок {p_id} успешно авторизован.")

def use_tool(cursor, player_id, tool, state, area, now):
    cfg = TOOLS[tool]

    cooldown_end = state["endsAt"]

    if state["charges"] == 0 and cooldown_end > now:
        return False

    max_charges = cfg.max_charges or 0

    new_charges = state["charges"] - 1 if state["charges"] > 0 else max_charges - 1
    new_cooldown = now if new_charges == 0 else 0

    cursor.execute(
        f"""
        UPDATE players
        SET {tool}_charges = ?,
            {tool}_cooldown_start = ?
        WHERE player_id = ?
        """,
        (new_charges, new_cooldown, player_id)
    )

    return True

def sanitize_sign_text(text: str) -> str:

    if not text:
        return ""

    text = re.sub(r"[^a-zA-Zа-яА-ЯёЁ ]+", "", text)

    text = re.sub(r"\s+", " ", text)

    text = text.strip()

    return text[:30]