from config import *

#вся эта хрень скоро будет удалена

def load_text_list(file_path, as_set=False):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip().lower() for line in f if line.strip()]
            return set(lines) if as_set else lines
    except FileNotFoundError:
        return set() if as_set else []

def load_json(path, default=None):
    default = default if default is not None else {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_images_data():
    data = load_json(IMAGES_JSON, default=None)
    if data is None or not data.get("all"):
        all_images = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]
        data = {"all": all_images, "used": []}
        save_json(IMAGES_JSON, data)
    return data