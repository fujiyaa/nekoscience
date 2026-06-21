


from .database import SettingsDatabase
from .defaults import SETTINGS

from config import BOT_DIR



class SettingsService:
    def __init__(self, database: SettingsDatabase):
        self.db = database

    def get(self, user_id: int, key: str):
        if key not in SETTINGS:
            raise KeyError(f"Unknown setting '{key}'")

        info = SETTINGS[key]
        default = info["default"]

        value = self.db.get(user_id, key)

        if value is None:
            return default

        return self._deserialize(value, key)

    def set(self, user_id: int, key: str, value):
        if key not in SETTINGS:
            raise KeyError(f"Unknown setting '{key}'")

        default = SETTINGS[key]["default"]

        if type(value) is not type(default):
            raise TypeError(
                f"{key} expects {type(default).__name__}, got {type(value).__name__}"
            )

        self.db.set(
            user_id,
            key,
            self._serialize(value)
        )

    def toggle(self, user_id: int, key: str) -> bool:
        if key not in SETTINGS:
            raise KeyError(f"Unknown setting '{key}'")

        default = SETTINGS[key]["default"]

        if not isinstance(default, bool):
            raise TypeError(f"{key} is not a bool setting")

        new_value = not self.get(user_id, key)
        self.set(user_id, key, new_value)

        return new_value

    def get_all(self, user_id: int) -> dict:
        raw = self.db.get_all(user_id)

        result = {}

        for key, info in SETTINGS.items():
            value = raw.get(key)

            if value is None:
                result[key] = info["default"]
            else:
                result[key] = self._deserialize(value, key)

        return result

    @staticmethod
    def _serialize(value):
        return str(int(value)) if isinstance(value, bool) else str(value)

    @staticmethod
    def _deserialize(value: str, key: str):
        default = SETTINGS[key]["default"]

        if isinstance(default, bool):
            return value == "1"

        if isinstance(default, int):
            return int(value)

        if isinstance(default, float):
            return float(value)

        return value
    
neko_settings_db = SettingsDatabase(BOT_DIR / "neko_settings.db")
neko_settings = SettingsService(neko_settings_db)
