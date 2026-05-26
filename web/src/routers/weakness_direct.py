from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/weakness/direct", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("weakness_direct.html", {"request": request})