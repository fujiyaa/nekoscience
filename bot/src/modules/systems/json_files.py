


import os, json

from config import SCORES_DIR



def get_score_path(score_id: str) -> str:
    return os.path.join(SCORES_DIR, f"{score_id}.json")
def load_score_file(score_id: str) -> dict | None:
    path = get_score_path(score_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠ Ошибка при загрузке файла {score_id}: {e}")
    return None
def save_score_file(score_id: str, data: dict):
    path = get_score_path(score_id)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠ Ошибка при сохранении файла {score_id}: {e}")