try {
    & ".\bot\src\venv\Scripts\Activate.ps1"
    python .\bot\src\main.py
} finally {
    deactivate
}