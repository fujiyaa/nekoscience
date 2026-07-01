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
import time
import functools
from contextlib import contextmanager
from functools import lru_cache
from typing import List, Set, Dict, Optional, Callable
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from collections import defaultdict, deque
import logging
from dataclasses import dataclass
import msgpack
from logging.handlers import RotatingFileHandler
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, Dict, Any
from starlette.websockets import WebSocketState, WebSocketDisconnect

templates = Jinja2Templates(directory="templates")
router = APIRouter()

DB_NAME = "game_v2.db"
BOT_TOKEN = os.getenv("TOKEN")

SIZE = 250
CELL = 50

GAME_GRID_CACHE = []
last_action_times = {}
GAME_STATE_CACHE = {}
CONTOUR_PATHS_CACHE = {}

DIRS = [(1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1)]

stone_alert_text = 'Здесь ничего нет'

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
    
class BaseToolHandler(ABC):
    @abstractmethod
    def validate(self, player_id: int, x: int, y: int, grid: list, 
                 state: Dict, payload: Dict) -> Tuple[bool, Optional[str]]:
        pass

    @abstractmethod
    def execute(self, player_id: int, x: int, y: int, grid: list, 
                payload: Dict, now: int) -> Tuple[List[Dict], List[Any]]:
        pass

class SignHandler(BaseToolHandler):
    def validate(self, player_id, x, y, grid, state, payload):
        text = sanitize_sign_text(payload.get("text", ""))
        if not text or len(text) > 30:
            return False, 'Текст слишком длинный'
        if not (0 <= y < len(grid) and 0 <= x < len(grid[0])):
            return False, 'За пределами мира'
        if grid[y][x].get("type") is not None:
            return False, 'Здесь чем-то занято'
        return True, None

    def execute(self, player_id, x, y, grid, payload, now):
        tool = payload["tool"]
        text = sanitize_sign_text(payload.get("text", ""))
        grid[y][x].update({
            "player_id": 0, "contour_id": -1,
            "type": {"id": "Sign", "data": text}
        })
        events = [
            {"tool": tool},
            {"msg": f"Появилась новая табличка", "msg_to": "all"},
            {"sfx": "sign"},
            {"cords": {
                "x": x,
                "y": y,
                "contour_id": grid[y][x]["contour_id"],
                "data": text,
                "radius": (SIZE/10),
                "player_id": player_id
            }}
        ]
        return events, [(x, y)]
    
class DrawHandler(BaseToolHandler):
    def __init__(self, size, get_neighbours_func, get_free_id_func):
        self.size = size
        self.get_neighbours = get_neighbours_func
        self.get_free_id = get_free_id_func

    def validate(self, player_id, x, y, grid, state, payload):
        if grid[y][x]["contour_id"] != 0:
            return False, 'Здесь уже занято'
        return True, None

    def execute(self, player_id, x, y, grid, payload, now):
        tool = payload["tool"]
        cell_type_id = "Dot" if tool == "draw" else "T2Dot"
        
        ids_to_refresh = set()
        
        neighbours = self.get_neighbours(x, y, player_id, grid)

        if len(neighbours) > 1:
            main_id = neighbours[0]
            ids_to_refresh.update(neighbours)

            for yy in range(self.size):
                for xx in range(self.size):
                    if grid[yy][xx]["contour_id"] in neighbours:
                        grid[yy][xx]["contour_id"] = main_id
            
            grid[y][x]["contour_id"] = main_id
        else:
            new_id = neighbours[0] if neighbours else self.get_free_id(grid)
            grid[y][x]["contour_id"] = new_id
            ids_to_refresh.add(new_id)

        grid[y][x]["player_id"] = player_id
        grid[y][x]["type"] = {"id": cell_type_id, "data": None}

        events = [
            {"tool": tool},
            {"sfx": "draw"},
            {"cords": {
                "x": x,
                "y": y,
                "contour_id": grid[y][x]["contour_id"],
                "radius": (SIZE/10),
                "player_id": player_id
            }}
        ]

        return events, ids_to_refresh

class StructureHandler(BaseToolHandler):
    def __init__(self, size, tools_cfg, get_cells_func, get_free_id_func):
        self.size = size
        self.tools_cfg = tools_cfg
        self.get_cells_in_radius = get_cells_func
        self.get_free_id = get_free_id_func

    def validate(self, player_id, x, y, grid, state, payload):
        if grid[y][x]["contour_id"] != 0:
            return False, 'Можно строить только на пустом'

        cfg = self.tools_cfg["structure"]
        check_radius = cfg.radius + cfg.radius
        
        for nx, ny in self.get_cells_in_radius(x, y, check_radius):
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if grid[ny][nx]["contour_id"] != 0:
                    return False, 'Структуре не хватает места'
        
        return True, None

    def execute(self, player_id, x, y, grid, payload, now):
        tool = payload["tool"]
        cfg = self.tools_cfg["structure"]
        radius = cfg.radius
        radius_expand = cfg.radius
        
        new_id = self.get_free_id(grid)
        
        for nx in range(x - radius, x + radius + radius_expand):
            for ny in range(y - radius, y + radius + radius_expand):
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if abs(nx - x) + abs(ny - y) == radius:
                        grid[ny][nx].update({
                            "contour_id": new_id,
                            "player_id": player_id,
                            "type": {"id": "T2Dot", "data": None}
                        })
        
        events = [
            {"tool": tool},
            {"sfx": "structure"},
            {"msg": f"Новый замок был построен ({x}, {y})", "msg_to": "all"},
            {"cords": {
                "x": x,
                "y": y,
                "structure_radius": radius,
                "radius": (SIZE/10),
                "player_id": player_id
            }}
        ]
        
        return events, {new_id}

class EraseHandler(BaseToolHandler):
    def __init__(self, recalculate_func):
        self.recalculate_func = recalculate_func

    def validate(self, player_id, x, y, grid, state, payload):
        tool = payload.get("tool")
               
        if grid[y][x]["contour_id"] == 0:
            return False, 'Не может начинаться с пустого места'
        
        cell = grid[y][x]
        cell_type = cell.get("type", {}).get("id")

        if cell["contour_id"] == 0 or cell_type == "Stone":
            return False, 'Здесь ничего нет'
        
        if tool == "erase" and cell_type in ["T2Dot", "Sign"]:
            return False, 'Это может ластик 2-го уровня'
            
        return True, None

    def execute(self, player_id, x, y, grid, payload, now):
        tool = payload["tool"]
        target_contour_id = grid[y][x]["contour_id"]
        target_pid = grid[y][x]["player_id"]
        
        grid[y][x].update({
            "contour_id": 0,
            "player_id": None,
            "type": None
        })
        
        ids_to_refresh = {target_contour_id}
        
        if target_pid:
            new_ids = self.recalculate_func(target_contour_id, target_pid, grid)
            ids_to_refresh.update(new_ids)
            
        events = [
            {"tool": tool},
            {"sfx": "erase"},
            {"cords": {
                "x": x,
                "y": y,                
                "contour_id": grid[y][x]["contour_id"],
                "radius": (SIZE/10),
                "player_id": player_id
            }}
        ]
        
        return events, ids_to_refresh

class BlastHandler(BaseToolHandler):
    def __init__(self, tools_cfg, get_cells_func, recalculate_func):
        self.tools_cfg = tools_cfg
        self.get_cells_in_radius = get_cells_func
        self.recalculate_player_contours_nearby = recalculate_func

    def validate(self, player_id, x, y, grid, state, payload):
        if grid[y][x]["contour_id"] == 0:
            return False, 'Не может начинаться с пустого места'
        return True, None

    def execute(self, player_id, x, y, grid, payload, now):
        tool = payload["tool"]
        cfg = self.tools_cfg[tool]
        radius = cfg.radius

        immune_types = ["Stone"]
        if tool == "blast":
            immune_types.extend(["T2Dot", "Sign"])

        affected_cells = list(self.get_cells_in_radius(x, y, radius))
        
        affected_contours = set()
        initial_contour_ids = set() 
        
        for nx, ny in affected_cells:
            cell = grid[ny][nx]
            cell_type = (cell.get("type") or {}).get("id")
            if cell["contour_id"] != 0 and cell_type not in immune_types:
                affected_contours.add((cell["player_id"], cell["contour_id"]))
                initial_contour_ids.add(cell["contour_id"])

        for nx, ny in affected_cells:
            cell = grid[ny][nx]
            if (cell.get("type") or {}).get("id") in immune_types:
                continue
            cell.update({"contour_id": 0, "player_id": None, "type": None})

        all_new_contour_ids = set()
        for pid, cid in affected_contours:
            new_ids = self.recalculate_player_contours_nearby(cid, pid, grid)
            if new_ids:
                all_new_contour_ids.update(new_ids)

        return_ids = all_new_contour_ids.union(initial_contour_ids)

        events = [
            {"tool": tool},
            {"msg": f"Что-то было взорвано ({x}, {y})", "msg_to": "all"},
            {"sfx": "blast"},
            {"cords": {
                "x": x,
                "y": y,
                "blast_radius": radius,
                "radius": (SIZE/10),
                "player_id": player_id
            }}
        ]
        
        return events, return_ids

def get_size_analysis(data):
    # Общий вес
    full_json = json.dumps(data)
    total_size = len(full_json.encode('utf-8'))
    
    output = [f"JSON | {total_size / 1024:.2f} KB"]
    
    if not isinstance(data, dict):
        return f"{type(data)} | {total_size / 1024:.2f} KB"

    for key, value in data.items():
        val_size = len(json.dumps({key: value}).encode('utf-8'))
        output.append(f".. {key}: {val_size / 1024:.2f} KB")
        
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                sub_size = len(json.dumps({sub_key: sub_val}).encode('utf-8'))
                output.append(f".... {sub_key}: {sub_size / 1024:.2f} KB")
        elif isinstance(value, list):
            output.append(f".... list: {len(value)} | {type(value[0]) if value else 'empty'}")

    return "\n".join(output)

    
class ActionPayload(BaseModel):
    player_id: int
    tool: str = Field(..., pattern="^(draw|erase|blast|sign|structure|tier2draw|tier2erase|tier2blast)$")
    x: int = Field(..., ge=0, lt=SIZE)
    y: int = Field(..., ge=0, lt=SIZE)
    text: Optional[str] = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    def _is_dead(self, conn):
        return getattr(conn, "client_state", None) is None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket) 

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        dead = set()

        for conn in self.active_connections:
            if getattr(conn, "client_state", None) is None:
                dead.add(conn)

        for d in dead:
            self.active_connections.discard(d)
        
        player_ids = [
            getattr(conn, "player_id", "Unknown")
            for conn in self.active_connections
        ]

        logger.info(
            f"WS BROADCAST START | sockets={len(self.active_connections)} | players={player_ids}"
        )
        
        # json_data = json.dumps(message)
        logger.info(get_size_analysis(message))

        packed_data = msgpack.packb(message, use_bin_type=True)

        connections = list(self.active_connections)
        
        for connection in connections:
            asyncio.create_task(self._send_to_one(connection, packed_data))

    async def _send_to_one(self, connection, data):
        if connection not in self.active_connections:
            return

        if getattr(connection, "client_state", None) != WebSocketState.CONNECTED:
            return

        start_time = time.perf_counter()
        player_id = getattr(connection, "player_id", "Unknown")
        
        try:
            await asyncio.wait_for(connection.send_bytes(data), timeout=1.0)
            
            duration = time.perf_counter() - start_time
            logger.info(f"Send to {player_id} занял {duration:.4f} сек")
            
        except asyncio.TimeoutError:
            logger.error(f"Таймаут отправки для {player_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки {player_id}: {e}")

    async def send_personal_event(self, player_id: int, msg_text: str, msg_level: str):
        for connection in self.active_connections:
            if getattr(connection, "player_id", None) == player_id:
                try:
                    message = {
                        "type": "update",
                        "data": None,
                        "events": [
                            {
                                "msg": msg_text,
                                "msg_to": player_id,
                                "msg_level": msg_level
                            }
                        ]
                    }
                    logger.info(f"WS: {player_id}: early exit (personal event)")                    
                    await connection.send_bytes(msgpack.packb(message, use_bin_type=True))                    
                except Exception as e:
                    logger.error(f"ConnectionManager | {player_id}: {e}")
                break

TOOLS = {
    "sign": ToolConfig(
        name="sign",
        base_cooldown_sec=1,
        max_charges=50,
    ),
    "structure": ToolConfig(
        name="structure",
        base_cooldown_sec=1,
        max_charges=50,
        radius=5,
    ),
    
    "draw": ToolConfig(
        name="draw",
        base_cooldown_sec=1,
        max_charges=50,
    ),
    "erase": ToolConfig(
        name="erase",
        base_cooldown_sec=2,
        max_charges=10,
        area_scaling=lambda area: (area // 100) * 3000,
    ),
    "blast": ToolConfig(
        name="blast",
        base_cooldown_sec=1,
        max_charges=50,
        radius=14,
    ),

    "tier2draw": ToolConfig(
        name="tier2draw",
        base_cooldown_sec=5,
        max_charges=30,
    ),
    "tier2erase": ToolConfig(
        name="tier2erase",
        base_cooldown_sec=5,
        max_charges=30,
        area_scaling=lambda area: (area // 100) * 3000,
    ),
    "tier2blast": ToolConfig(
        name="tier2blast",
        base_cooldown_sec=5,
        max_charges=10,
        radius=6,
    ),
}

manager = ConnectionManager()

class MaxLinesFileHandler(logging.FileHandler):
    def __init__(self, filename, max_lines=30, *args, **kwargs):
        self.max_lines = max_lines
        super().__init__(filename, *args, **kwargs)

    def emit(self, record):
        super().emit(record)
        
        with open(self.baseFilename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if len(lines) > self.max_lines:
            with open(self.baseFilename, 'w', encoding='utf-8') as f:
                f.writelines(lines[-self.max_lines:])

logger = logging.getLogger("game_ws")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = RotatingFileHandler(
    "game.log",
    maxBytes=100_000,
    backupCount=1,
    encoding="utf-8"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

def log_execution_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start_time
        logger.info(f"{duration:.4f} | {func.__name__}")
        return result
    return wrapper

@contextmanager
def timer(name):
    start = time.perf_counter()
    yield
    duration = time.perf_counter() - start
    logger.info(f"{duration:.4f} | {name}")

@log_execution_time
def load_external_passwords():
    path = os.path.join(os.path.dirname(DB_NAME), "miniapp_passwords.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Не удалось прочитать external passwords: {e}")
        return {}

@log_execution_time
def validate_telegram_data(init_data: str) -> bool:
    parsed_data = urllib.parse.parse_qs(init_data)
    if 'hash' not in parsed_data:
        return False    
    received_hash = parsed_data.pop('hash')[0]    
    data_check_string = "\n".join([f"{k}={v[0]}" for k, v in sorted(parsed_data.items())])    
    secret_key = hmac.new("WebAppData".encode(), BOT_TOKEN.encode(), hashlib.sha256).digest()    
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()    
    return hmac.compare_digest(calculated_hash, received_hash)

@log_execution_time
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
                type_data TEXT,     -- данные
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

def batch_update_cell_ownership(cursor, updates: List[dict]):
    if not updates:
        return

    to_upsert = [
        (u['x'], u['y'], u['player_id'], u['contour_id']) 
        for u in updates if u['player_id'] is not None
    ]
    
    to_delete = [(u['x'], u['y']) for u in updates if u['player_id'] is None]

    if to_upsert:
        cursor.executemany("""
            INSERT INTO cells (x, y, player_id, contour_id) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(x, y) DO UPDATE SET 
                player_id=excluded.player_id, 
                contour_id=excluded.contour_id
        """, to_upsert)

    if to_delete:
        cursor.executemany("""
            DELETE FROM cells WHERE x = ? AND y = ?
        """, to_delete)

def batch_update_cell_types(cursor, updates: List[dict]):
    if not updates:
        return

    data_to_upsert = [
        (u['x'], u['y'], u['type_id'], str(u['data']) if u['data'] else None)
        for u in updates if u['type_id'] is not None
    ]
    
    to_delete = [(u['x'], u['y']) for u in updates if u['type_id'] is None]

    if data_to_upsert:
        cursor.executemany("""
            INSERT INTO cell_types (x, y, type_id, type_data)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(x, y) DO UPDATE SET 
                type_id=excluded.type_id, 
                type_data=excluded.type_data
        """, data_to_upsert)

    if to_delete:
        cursor.executemany("""
            DELETE FROM cell_types WHERE x = ? AND y = ?
        """, to_delete)

@log_execution_time
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
        "type": {"id": row[2], "data": row[3] if row[3] else None}
    }

_GRID_CACHE = None

@log_execution_time
def load_grid_from_db(cursor, force_reload=False) -> List[List[dict]]:
    global _GRID_CACHE
    
    # if _GRID_CACHE is not None and not force_reload:
    #     return _GRID_CACHE
    
    cursor.execute("DELETE FROM cells WHERE x >= ? OR y >= ?", (SIZE, SIZE))
    cursor.execute("DELETE FROM cell_types WHERE x >= ? OR y >= ?", (SIZE, SIZE))

    grid = [[{"player_id": None, "contour_id": 0, "type": None} for _ in range(SIZE)] for _ in range(SIZE)]
    
    query = """
        SELECT c.x, c.y, c.player_id, c.contour_id, t.type_id, t.type_data 
        FROM cells c 
        LEFT JOIN cell_types t ON c.x = t.x AND c.y = t.y
        WHERE c.x < ? AND c.y < ?
    """
    cursor.execute(query, (SIZE, SIZE))
    
    for x, y, p_id, c_id, t_id, t_data in cursor:
        grid[y][x] = {
            "player_id": p_id,
            "contour_id": c_id,
            "type": {
                "id": t_id, 
                "data": t_data if t_data else None
            } if t_id is not None else None
        }
            
    _GRID_CACHE = grid
    return _GRID_CACHE

@log_execution_time
def update_cache_cell(x, y, new_data: dict):
    global GAME_GRID_CACHE
    GAME_GRID_CACHE[y][x].update(new_data)

@log_execution_time
def sync_grid_to_db(cursor, new_grid: List[List[dict]]):
    global GAME_GRID_CACHE

    updates_to_process = []
    ownership_updates = []
    
    for y in range(SIZE):
        for x in range(SIZE):
            new_cell = new_grid[y][x]
            old_cell = GAME_GRID_CACHE[y][x]
            
            if (new_cell["player_id"] != old_cell["player_id"] or 
                new_cell["contour_id"] != old_cell["contour_id"]):                

                ownership_updates.append({
                    'x': x, 'y': y, 
                    'player_id': new_cell["player_id"], 
                    'contour_id': new_cell["contour_id"]
                })
                GAME_GRID_CACHE[y][x].update(
                    {"player_id": new_cell["player_id"], "contour_id": new_cell["contour_id"]}
                )

            if new_cell["type"] != old_cell["type"]:
                updates_to_process.append({
                    'x': x, 'y': y, 
                    'type_id': new_cell["type"]["id"] if new_cell["type"] else None,
                    'data': new_cell["type"]["data"] if new_cell["type"] else None
                })

                GAME_GRID_CACHE[y][x]["type"] = new_cell["type"]

    batch_update_cell_ownership(cursor, ownership_updates)
    batch_update_cell_types(cursor, updates_to_process)        

init_db()

@log_execution_time
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

@log_execution_time
def get_free_contour_id(grid: List[List[dict]]) -> int:
    used_ids = {
        cell["contour_id"] 
        for row in grid 
        for cell in row 
        if cell["contour_id"] != 0
    }
    
    contour_id = 1
    while contour_id in used_ids:
        contour_id += 1
        
    return contour_id

@log_execution_time
def get_neighbour_contours(x: int, y: int, player_id: int, grid: List[List[dict]]) -> List[int]:

    neighbours = set()
    for dx, dy in DIRS:
        nx, ny = x + dx, y + dy
        if in_bounds(nx, ny):
            cell = grid[ny][nx]
            if cell["player_id"] == player_id and cell["contour_id"] != 0:
                neighbours.add(cell["contour_id"])

    return list(neighbours)

@log_execution_time
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
            new_id = get_free_contour_id(grid)
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

def build_mask(grid: List[List[dict]], contour_id: int) -> List[List[int]]:
    return [
        [1 if cell["contour_id"] == contour_id else 0 for cell in row]
        for row in grid
    ]

def build_mask_and_count(grid: List[List[dict]], contour_id: int):
    mask = []
    count = 0
    for row in grid:
        mask_row = []
        for cell in row:
            if cell["contour_id"] == contour_id:
                mask_row.append(1)
                count += 1
            else:
                mask_row.append(0)
        mask.append(mask_row)
    return mask, count

@lru_cache(maxsize=SIZE*SIZE)
def cached_trace(mask_tuple):
    mask_list = [list(row) for row in mask_tuple]
    return trace_contour(mask_list)

def get_trace_from_cache(mask: List[List[int]]):
    mask_key = tuple(tuple(row) for row in mask)
    return cached_trace(mask_key)

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

@log_execution_time
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

@log_execution_time
def refresh_contour_cache(grid: List[List[dict]], ids_to_update: Optional[Set[int]] = None):
    global CONTOUR_PATHS_CACHE  
    updated_ids = {}

    existing_ids = {cell["contour_id"] for row in grid for cell in row if cell["contour_id"] != 0}

    if ids_to_update is not None:
        for c_id in ids_to_update:
            if c_id in existing_ids:
                mask, count = build_mask_and_count(grid, c_id)
                logger.info(f'{c_id}, {count}')
                updated_ids[c_id] = CONTOUR_PATHS_CACHE[c_id] = trace_contour(mask)
            elif c_id in CONTOUR_PATHS_CACHE:
                del CONTOUR_PATHS_CACHE[c_id]
                updated_ids[c_id] = None                
    else:
        CONTOUR_PATHS_CACHE.clear()
        for c_id in existing_ids:
            mask, count = build_mask_and_count(grid, c_id)
            updated_ids[c_id] = CONTOUR_PATHS_CACHE[c_id] = trace_contour(mask)

    return updated_ids    
    
def get_current_state_dict():
    global GAME_STATE_CACHE

    if not GAME_STATE_CACHE:
        refresh_game_state_cache()
    return GAME_STATE_CACHE

@log_execution_time
def refresh_game_state_cache(updated_contour_ids: Optional[Set[int]] = None):
    global GAME_STATE_CACHE

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        grid = load_grid_from_db(cursor)
        
        paths_updated = refresh_contour_cache(grid, updated_contour_ids)

        updated_ids = {}        
        contour_to_player = {}

        for row in grid:
            for cell in row:
                c_id = cell["contour_id"]
                if c_id != 0 and c_id not in contour_to_player:
                    contour_to_player[c_id] = cell["player_id"]

        for c_id, path in paths_updated.items():
            if path is None:
                updated_ids[c_id] = None
            else:
                updated_ids[c_id] = {
                    "playerId": contour_to_player.get(c_id),
                    "path": path
                }
        
        serialized_contours = []
        player_areas = defaultdict(float)
        
        for c_id, path in CONTOUR_PATHS_CACHE.items():
            p_id = contour_to_player.get(c_id)
            area = calculate_contour_area(path)
            
            if p_id is not None:
                player_areas[p_id] += area
            
        serialized_contours = [
            {
                "id": c_id,
                "playerId": contour_to_player.get(c_id),
                "path": path
            } 
            for c_id, path in CONTOUR_PATHS_CACHE.items()
        ]
        
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

    return updated_ids

def get_player_total_area_from_cache(player_id: int) -> float:
    if GAME_STATE_CACHE:
        for entry in GAME_STATE_CACHE.get("leaderboard", []):
            if entry["player_id"] == player_id:
                return entry["totalArea"]
    return 0.0

HANDLERS = {
    "sign": SignHandler(),
    "draw": DrawHandler(SIZE, get_neighbour_contours, get_free_contour_id),
    "tier2draw": DrawHandler(SIZE, get_neighbour_contours, get_free_contour_id),
    "structure": StructureHandler(SIZE, TOOLS, get_cells_in_radius, get_free_contour_id),
    "erase": EraseHandler(recalculate_player_contours_nearby),
    "tier2erase": EraseHandler(recalculate_player_contours_nearby),
    "blast": BlastHandler(TOOLS, get_cells_in_radius, recalculate_player_contours_nearby),
    "tier2blast": BlastHandler(TOOLS, get_cells_in_radius, recalculate_player_contours_nearby),
}

@router.get("/game", response_class=HTMLResponse)
async def game(request: Request):
    return templates.TemplateResponse("game.html", {"request": request})

@router.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    websocket.player_id = None
    logger.info("WS: Новый")

    try:
        while True:
            if websocket.client_state == WebSocketState.DISCONNECTED:
                break

            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            if "bytes" in message:
                data_bytes = message["bytes"]           
            else:
                continue

            try:
                data = msgpack.unpackb(data_bytes, raw=False) # raw=False для корректного декодирования строк
            except Exception as e:
                logger.error(f"Ошибка декодирования MessagePack: {e}")
                continue

            msg_type = data.get("type")
            start_time = time.perf_counter()

            if msg_type == "ping":
                await websocket.send_bytes(msgpack.packb({"type": "pong"}, use_bin_type=True))
                continue
            else:
                logger.info(f"WS: {msg_type} (start)")

            if msg_type == "auth":
                init_data = data.get("initData")
                if not init_data or not validate_telegram_data(init_data):
                    await websocket.send_bytes(msgpack.packb({"type": "error", "message": "Invalid Authorization"}, use_bin_type=True))
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
                    await websocket.send_bytes(msgpack.packb({"type": "error", "message": "Invalid Authorization"}, use_bin_type=True))
                    continue
                    
                await perform_player_auth(websocket, match[0], match[1].get("name", "Player"))
                continue

            if msg_type == "get_init":
                state = get_current_state_dict()
                await websocket.send_bytes(msgpack.packb({"type": "init", "data": state}, use_bin_type=True))
                continue

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
                    
                    ids_to_refresh = set()
                    events = []
                    
                    handler = HANDLERS.get(tool)
                    if not handler:
                        continue                    

                    with sqlite3.connect(DB_NAME) as conn:
                        cursor = conn.cursor()
                        
                        grid = load_grid_from_db(cursor)
                        player_area = get_player_total_area_from_cache(player_id)

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

                        if not can_use_tool(tool_state[tool], now):
                            await manager.send_personal_event(player_id, 'На перезарядке', 'tip')
                            continue

                        is_valid, error = handler.validate(player_id, x, y, grid, tool_state[tool], data["payload"])
                        if not is_valid:
                            await manager.send_personal_event(player_id, error, 'warn')
                            continue

                        consume_tool_charge(cursor, player_id, tool, TOOLS[tool], tool_state[tool], now)

                        events, ids_to_refresh = handler.execute(player_id, x, y, grid, data["payload"], now)                       
                        
                        # is_valid
                        sync_grid_to_db(cursor, grid)
                        conn.commit()

                    updated_ids = refresh_game_state_cache(updated_contour_ids=ids_to_refresh)
                    
                    message = {
                        "type": "update",
                        "events": events,
                        "updated_contours": updated_ids or {}
                    }
                    
                    duration = time.perf_counter() - start_time
                    logger.info(f"{duration:.4f} - in total | WS sending")
                    await manager.broadcast(message)
                        
                except Exception as e:
                    logger.error(f"WS: {e}\n{traceback.format_exc()}")
        
            duration = time.perf_counter() - start_time
            logger.info(f"{duration:.4f} | WS {msg_type}")

    except WebSocketDisconnect:
        logger.info(f"WS: Отключен ({getattr(websocket, 'player_id', 'Unknown')})")
    except RuntimeError as e:
        logger.warning(f"WS: {e}\n{traceback.format_exc()}")
    except Exception as e:
        logger.error(f"WS: {e}\n{traceback.format_exc()}")
    finally:
        manager.disconnect(websocket)
            
async def perform_player_auth(websocket, p_id: int, username: str):
    old_conns = [conn for conn in manager.active_connections 
                 if getattr(conn, "player_id", None) == p_id and conn != websocket]
    
    for conn in old_conns:
        try:
            await conn.send_bytes(msgpack.packb({"type": "session_replaced"}, use_bin_type=True))
            await asyncio.sleep(0.1) 
            await conn.close()
        except Exception:
            pass
        finally:
            manager.active_connections.discard(conn)
    
    websocket.player_id = p_id
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _sync_db_auth, p_id, username)
    
    await websocket.send_bytes(msgpack.packb({"type": "auth_success", "player_id": p_id}, use_bin_type=True))
       
    logger.info(f"WS: {p_id} авторизован")

def _sync_db_auth(p_id, username):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            INSERT INTO players (player_id, username) VALUES (?, ?)
            ON CONFLICT(player_id) DO UPDATE SET username=excluded.username
        """, (p_id, username))

def can_use_tool(tool_state, now) -> bool:
    cooldown_end = tool_state["endsAt"]
    
    if tool_state["charges"] == 0 and cooldown_end > now:
        return False
    return True

def consume_tool_charge(cursor, player_id, tool, cfg, state, now):
    max_charges = cfg.max_charges or 0
    current_charges = state["charges"]

    new_charges = current_charges - 1 if current_charges > 0 else max_charges - 1
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

def sanitize_sign_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"[^a-zA-Zа-яА-ЯёЁ0-9 ]+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text[:30]