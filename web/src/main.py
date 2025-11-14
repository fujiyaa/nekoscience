from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import random
from datetime import datetime, timedelta
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/data")
async def get_data(period: str = "day"):
    now = datetime.now()

    if period == "day":
        labels = [(now - timedelta(hours=i)).strftime("%H:%M") for i in range(23, -1, -1)]
    elif period == "week":
        labels = [(now - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
    else:
        labels = [(now - timedelta(days=i)).strftime("%d.%m") for i in range(29, -1, -1)]

    def rand3():
        return {
            "A": [random.randint(10, 100) for _ in labels],
            "B": [random.randint(10, 100) for _ in labels],
            "C": [random.randint(10, 100) for _ in labels],
        }

    all_stats = {
        "warns": random.randint(0, 10),
        "avg_value": random.randint(10000, 100000),
        "errors": random.randint(0, 30),
        "uptime": f"{round(random.uniform(97, 100), 2)}%",
    }

    data = {
        "labels": labels,
        "datasets": {
            "line": rand3(),
            "bar": rand3(),
            "radar": rand3(),
            "pie": {"A": [random.randint(10, 40) for _ in range(3)]},
            "doughnut": {"A": [random.randint(10, 40) for _ in range(3)]},
            "polar": {"A": [random.randint(10, 40) for _ in range(3)]},
            "bubble": {
                "A": [{"x": i, "y": random.randint(10, 100), "r": random.randint(5, 15)} for i in range(10)],
                "B": [{"x": i, "y": random.randint(10, 100), "r": random.randint(5, 15)} for i in range(10)],
                "C": [{"x": i, "y": random.randint(10, 100), "r": random.randint(5, 15)} for i in range(10)],
            },
            "scatter": {
                "A": [{"x": random.randint(0, 100), "y": random.randint(0, 100)} for _ in range(20)],
                "B": [{"x": random.randint(0, 100), "y": random.randint(0, 100)} for _ in range(20)],
                "C": [{"x": random.randint(0, 100), "y": random.randint(0, 100)} for _ in range(20)],
            },
        },
        "all_stats": all_stats,
    }

    return data
