& ".\web\src\venv\Scripts\Activate.ps1"
Set-Location ".\web\src"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
