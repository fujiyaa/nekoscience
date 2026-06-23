import math
import sqlite3
import time
from typing import List, Set, Dict, Optional
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter()

DB_NAME = "game.db"
SIZE = 200
CELL = 50

DIRS = [(1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1), (0,-1), (1,-1)]

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_grid (
                x INTEGER, y INTEGER, contour_id INTEGER DEFAULT 0, PRIMARY KEY (x, y)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY,
                draw_charges INTEGER DEFAULT 5,
                draw_cooldown_start REAL DEFAULT 0,
                erase_cooldown_start REAL DEFAULT 0
            )
        """)
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM game_grid")
        if cursor.fetchone()[0] == 0:
            grid_data = [(x, y, 0) for y in range(SIZE) for x in range(SIZE)]
            cursor.executemany("INSERT INTO game_grid (x, y, contour_id) VALUES (?, ?, ?)", grid_data)
            for p_id in range(1, 5):
                cursor.execute("INSERT OR IGNORE INTO players (player_id) VALUES (?)", (p_id,))
            conn.commit()

init_db()


def get_player_by_contour(contour_id: int) -> Optional[int]:
    if contour_id == 0:
        return None
    return contour_id // 10000

def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < SIZE and 0 <= y < SIZE

def load_grid_from_db(cursor) -> List[List[int]]:
    cursor.execute("SELECT x, y, contour_id FROM game_grid")
    grid = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
    for x, y, c_id in cursor.fetchall():
        grid[y][x] = c_id
    return grid

def save_grid_to_db(cursor, grid: List[List[int]]):
    for y in range(SIZE):
        for x in range(SIZE):
            cursor.execute("UPDATE game_grid SET contour_id = ? WHERE x = ? AND y = ?", (grid[y][x], x, y))

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
    """Поиск подграфов (связных областей) после удаления точки ластиком"""
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




def get_current_state_dict():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        grid = load_grid_from_db(cursor)
        
        
        unique_ids = {cell for row in grid for cell in row if cell != 0}
        
        
        serialized_contours = []
        player_areas = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        
        for c_id in unique_ids:
            mask = build_mask(grid, c_id)
            path = trace_contour(mask)
            area = calculate_contour_area(path)
            
            p_id = get_player_by_contour(c_id)
            if p_id in player_areas:
                player_areas[p_id] += area
                
            serialized_contours.append({
                "id": c_id,
                "player_id": p_id,
                "path": path
            })
        
        
        cursor.execute("SELECT player_id, draw_charges, draw_cooldown_start, erase_cooldown_start FROM players")
        players_data = {}
        now = time.time()
        
        for p_id, charges, d_start, e_start in cursor.fetchall():
            d_current = max(0, int((d_start + 10 - now) * 1000)) if d_start > 0 else 0
            if d_start > 0 and d_current == 0 and charges == 0:
                charges = 5
                cursor.execute("UPDATE players SET draw_charges = 5, draw_cooldown_start = 0 WHERE player_id = ?", (p_id,))
            
            e_current = max(0, int((e_start + 2 - now) * 1000)) if e_start > 0 else 0
            
            players_data[p_id] = {
                "cooldowns": {
                    "draw": {"charges": charges, "maxCharges": 5, "current": d_current, "max": 10000},
                    "erase": {"current": e_current, "max": 2000}
                }
            }
        conn.commit()
        
    
    leaderboard = [
        {"player_id": p_id, "totalArea": area} 
        for p_id, area in player_areas.items()
    ]
    
    leaderboard.sort(key=lambda x: x["totalArea"], reverse=True)

    return {
        "config": {
            "size": SIZE,
            "cell": CELL
        },
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

@router.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await websocket.send_json({"type": "init", "data": get_current_state_dict()})
    
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "action":
                payload = data["payload"]
                player_id = int(payload["player_id"])
                tool = payload["tool"]
                x, y = int(payload["x"]), int(payload["y"])
                
                if not in_bounds(x, y):
                    continue
                
                now = time.time()
                
                with sqlite3.connect(DB_NAME) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT draw_charges, draw_cooldown_start, erase_cooldown_start FROM players WHERE player_id = ?", (player_id,))
                    player_row = cursor.fetchone()
                    
                    if player_row:
                        charges, d_start, e_start = player_row
                        grid = load_grid_from_db(cursor)
                        action_valid = False
                        
                        
                        if tool == "draw" and grid[y][x] == 0:
                            if charges > 0 or (d_start + 10) <= now:
                                action_valid = True
                                neighbours = get_neighbour_contours(x, y, player_id, grid)
                                
                                if len(neighbours) == 0:
                                    grid[y][x] = get_free_contour_id(grid, player_id)
                                elif len(neighbours) == 1:
                                    grid[y][x] = neighbours[0]
                                else:
                                    
                                    main_id = neighbours[0]
                                    for yy in range(SIZE):
                                        for xx in range(SIZE):
                                            if grid[yy][xx] in neighbours:
                                                grid[yy][xx] = main_id
                                    grid[y][x] = main_id
                                
                                new_charges = charges - 1 if charges > 0 else 4
                                new_d_start = now if new_charges == 0 else 0
                                cursor.execute("UPDATE players SET draw_charges = ?, draw_cooldown_start = ? WHERE player_id = ?", (new_charges, new_d_start, player_id))
                        
                        
                        elif tool == "erase" and grid[y][x] != 0:
                            if (e_start + 2) <= now:
                                action_valid = True
                                target_contour_id = grid[y][x]
                                target_player_id = get_player_by_contour(target_contour_id)
                                
                                grid[y][x] = 0
                                
                                
                                if target_player_id is not None:
                                    recalculate_player_contours(target_player_id, grid)
                                    
                                cursor.execute("UPDATE players SET erase_cooldown_start = ? WHERE player_id = ?", (now, player_id))
                        
                        if action_valid:
                            save_grid_to_db(cursor, grid)
                            conn.commit()
                
                
                await manager.broadcast({"type": "update", "data": get_current_state_dict()})

    except WebSocketDisconnect:
        manager.disconnect(websocket)