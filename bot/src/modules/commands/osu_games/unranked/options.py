m_file = "file_osugames_matches"
d_file = "file_osugames_elo"

BANNER_OPTIONS = [
    "https://i.ibb.co/LXLsx9HL/image-10.png",
]

MAIN_MENU_TEXT = ""

MAIN_MENU_MYACTIVE_NONE = "Нет игр с твоим участием"

MAIN_MENU_MYACTIVE_SOME = "Игры с твоим участием"

MAIN_MENU_MYACTIVE_LIMIT = "Лимит количества игр, удали что-то"

SOURCE_OPTIONS = [
    "⤴️ Против скора",
    "🆚 Играют оба"
]

GOAL_OPTIONS = [
    "🆕 SCORE-V2",
    "👨‍🦳 SCORE-STD",
    "🏹 Точность",
    "❌ Миссы",
    "🔗 Комбо"
]

TIME_OPTIONS = [
    "⏳ Таймер 1 ч.",
    "⏳ Таймер 2 ч.",
    "⏳ Таймер 3 ч.",
    "⏳ Таймер 6 ч.",
    "⏳ Таймер 12 ч.",
    "⏳ Таймер 24 ч.",
    "⏳ Таймер 48 ч."
]

CROSSCLIENT_OPTIONS = [
    # "◽️ Любой клиент",
    "🔹Лазер клиент",
    "🔸Стейбл клиент"
]

MOD_LAYOUT_STABLE = [
    [   "EZ",   "NF",   "HT",   None,   None,   "FM"],
    [   "HR",   "HD",   "DT",   "NC",   None,   None],
    [   "SO",   "FL",   None,   None,   None, "RESET"],
    ["⬅️ Назад"]
]

MOD_LAYOUT_LAZER = [
    [   "EZ",   "NF",   "HT",   None,   None,   "FM"],
    [   "HR",   "HD",   "DT",   "NC",   None,   "CL"],
    [   "SO",   "FL",   "RX",   "AP",   None, "RESET"],
    ["⬅️ Назад"]
]

MOD_OPTIONS = [
        "EZ",   "NF",   "HT",                   "FM",
        "HR",   "HD",   "DT",   "NC",           "CL",
        "SO",   "FL",   "RX",   "AP"
]

INCOMPATIBLE_MODS = {
    "DT": {"HT", "NC"},
    "HT": {"DT", "NC"},
    "NC": {"HT", "DT"},

    "HR": {"EZ"},
    "EZ": {"HR"},

    "RX": {"AP"},

    "AP": {"RX", "SO"},

    "SO": {"AP"},
}

from telegram import LinkPreviewOptions
link_preview = LinkPreviewOptions(
            url=BANNER_OPTIONS[0],
            is_disabled=False,
            prefer_small_media=False,
            prefer_large_media=True,
            show_above_text=True
        )