import random
import sqlite3
import traceback
import json

from telegram import Update,  MessageEntity
from telegram.ext import ContextTypes

import time

DB_PATH = "ecos.db"

ACTIVITIES = {
    "fish": {
        "name": "🎣 Рыбалка",
        "good_action": "Поймано",
        "fail_action": "Ничего не поймано",
        "cooldown": 20,
        "level_field": "fish_level",
        "xp_field": "fish_xp",
        "fail_chance": 0.30,

        "loot": [
{"id": "fish_okun", "name": "🐟 Окунь", "min_level": 1, "weight": 70, "coins": (6, 12), "xp": 6, "rarity": "обычное"},
{"id": "fish_karp", "name": "🐠 Карп", "min_level": 1, "weight": 60, "coins": (10, 20), "xp": 10, "rarity": "обычное"},
{"id": "fish_som", "name": "🐡 Сом", "min_level": 1, "weight": 25, "coins": (20, 40), "xp": 20, "rarity": "редкое"},
{"id": "fish_lesh", "name": "🐟 Лещ", "min_level": 3, "weight": 40, "coins": (12, 22), "xp": 12, "rarity": "обычное"},
{"id": "fish_pike", "name": "🐊 Щука", "min_level": 5, "weight": 20, "coins": (25, 50), "xp": 25, "rarity": "редкое"},
{"id": "fish_ugor", "name": "🐍 Угорь", "min_level": 2, "weight": 15, "coins": (30, 60), "xp": 30, "rarity": "редкое"},
{"id": "fish_tuna", "name": "🐟 Тунец", "min_level": 6, "weight": 18, "coins": (35, 70), "xp": 35, "rarity": "редкое"},
{"id": "fish_swordfish", "name": "🗡 Рыба-меч", "min_level": 8, "weight": 8, "coins": (70, 130), "xp": 60, "rarity": "легендарное"},
{"id": "fish_electric_eel", "name": "⚡ Электрический угорь", "min_level": 7, "weight": 10, "coins": (60, 120), "xp": 55, "rarity": "легендарное"},
{"id": "fish_goldfish", "name": "🐠 Золотая рыбка", "min_level": 9, "weight": 3, "coins": (150, 300), "xp": 80, "rarity": "легендарное"},

{"id": "fish_catfish_giant", "name": "🐡 Гигантский сом", "min_level": 10, "weight": 5, "coins": (120, 220), "xp": 90, "rarity": "легендарное"},
{"id": "fish_salmon", "name": "🐟 Лосось", "min_level": 4, "weight": 35, "coins": (18, 35), "xp": 18, "rarity": "редкое"},
{"id": "fish_bass", "name": "🐟 Басс", "min_level": 3, "weight": 45, "coins": (10, 18), "xp": 10, "rarity": "обычное"},
{"id": "fish_mackerel", "name": "🐟 Скумбрия", "min_level": 2, "weight": 55, "coins": (8, 16), "xp": 8, "rarity": "обычное"},
{"id": "fish_halibut", "name": "🐟 Палтус", "min_level": 6, "weight": 20, "coins": (40, 80), "xp": 40, "rarity": "редкое"},
{"id": "fish_sturgeon", "name": "🐟 Осётр", "min_level": 8, "weight": 12, "coins": (80, 150), "xp": 70, "rarity": "легендарное"},
{"id": "fish_piranha", "name": "🩸 Пиранья", "min_level": 5, "weight": 18, "coins": (20, 45), "xp": 25, "rarity": "редкое"},
{"id": "fish_clownfish", "name": "🐠 Рыба-клоун", "min_level": 1, "weight": 65, "coins": (5, 10), "xp": 5, "rarity": "обычное"},
{"id": "fish_blobfish", "name": "🫠 Рыба-капля", "min_level": 7, "weight": 6, "coins": (50, 110), "xp": 50, "rarity": "легендарное"},
{"id": "fish_manta_ray", "name": "🪶 Скаты-манта", "min_level": 9, "weight": 4, "coins": (100, 200), "xp": 85, "rarity": "легендарное"},

{"id": "fish_arowana", "name": "🐟 Аравана", "min_level": 6, "weight": 14, "coins": (45, 90), "xp": 40, "rarity": "редкое"},
{"id": "fish_zander", "name": "🐟 Судак", "min_level": 5, "weight": 16, "coins": (35, 70), "xp": 35, "rarity": "редкое"},
{"id": "fish_roach_large", "name": "🐟 Крупная плотва", "min_level": 3, "weight": 22, "coins": (20, 40), "xp": 18, "rarity": "редкое"},
{"id": "fish_chub", "name": "🐟 Голавль", "min_level": 4, "weight": 18, "coins": (25, 55), "xp": 30, "rarity": "редкое"},
{"id": "fish_dace", "name": "🐟 Язь", "min_level": 4, "weight": 17, "coins": (28, 60), "xp": 32, "rarity": "редкое"},
{"id": "fish_grayling", "name": "🐟 Хариус", "min_level": 6, "weight": 12, "coins": (40, 85), "xp": 45, "rarity": "редкое"},
{"id": "fish_perch_king", "name": "🐟 Королевский окунь", "min_level": 7, "weight": 10, "coins": (55, 110), "xp": 55, "rarity": "редкое"},
{"id": "fish_catfish_black", "name": "🐡 Чёрный сом", "min_level": 7, "weight": 9, "coins": (60, 120), "xp": 60, "rarity": "редкое"},
{"id": "fish_eel_american", "name": "🐍 Американский угорь", "min_level": 6, "weight": 13, "coins": (50, 100), "xp": 50, "rarity": "редкое"},
{"id": "fish_trout_rainbow", "name": "🐟 Радужная форель", "min_level": 4, "weight": 20, "coins": (30, 65), "xp": 30, "rarity": "редкое"},

{"id": "fish_walleye", "name": "🐟 Судак озёрный", "min_level": 6, "weight": 14, "coins": (45, 95), "xp": 45, "rarity": "редкое"},
{"id": "fish_bream_silver", "name": "🐟 Серебряный лещ", "min_level": 5, "weight": 15, "coins": (35, 75), "xp": 38, "rarity": "редкое"},
{"id": "fish_pike_perch", "name": "🐊 Щукоокунь", "min_level": 7, "weight": 9, "coins": (60, 130), "xp": 60, "rarity": "редкое"},
{"id": "fish_silverside", "name": "🐟 Сребрянка", "min_level": 3, "weight": 25, "coins": (18, 35), "xp": 15, "rarity": "редкое"},
{"id": "fish_snakehead", "name": "🐍 Змееголов", "min_level": 7, "weight": 8, "coins": (70, 140), "xp": 65, "rarity": "редкое"},
{"id": "fish_garfish", "name": "🐟 Игла-рыба", "min_level": 6, "weight": 11, "coins": (55, 110), "xp": 50, "rarity": "редкое"},
{"id": "fish_barracuda_small", "name": "🦈 Молодая барракуда", "min_level": 7, "weight": 9, "coins": (65, 130), "xp": 60, "rarity": "редкое"},
{"id": "fish_freshwater_drum", "name": "🐟 Пресноводный барабанщик", "min_level": 5, "weight": 13, "coins": (40, 80), "xp": 40, "rarity": "редкое"},
{"id": "fish_opah_small", "name": "🐟 Малый опах", "min_level": 6, "weight": 10, "coins": (50, 100), "xp": 45, "rarity": "редкое"},
{"id": "fish_tench", "name": "🐟 Линь", "min_level": 4, "weight": 19, "coins": (25, 55), "xp": 28, "rarity": "редкое"},

{"id": "fish_mahi_mahi", "name": "🐟 Махи-махи", "min_level": 10, "weight": 14, "coins": (60, 120), "xp": 55, "rarity": "редкое"},
{"id": "fish_red_snapper", "name": "🐟 Красный снэппер", "min_level": 12, "weight": 13, "coins": (70, 140), "xp": 60, "rarity": "редкое"},
{"id": "fish_groupers", "name": "🐟 Групер", "min_level": 15, "weight": 12, "coins": (80, 160), "xp": 70, "rarity": "редкое"},
{"id": "fish_tilapia", "name": "🐟 Тилапия", "min_level": 10, "weight": 18, "coins": (55, 110), "xp": 50, "rarity": "редкое"},
{"id": "fish_catfish_nile", "name": "🐡 Нильский сом", "min_level": 18, "weight": 10, "coins": (100, 200), "xp": 85, "rarity": "редкое"},

{"id": "fish_arapaima", "name": "🐟 Арапайма", "min_level": 25, "weight": 6, "coins": (180, 350), "xp": 150, "rarity": "легендарное"},
{"id": "fish_pirarucu", "name": "🐟 Пираруку", "min_level": 28, "weight": 5, "coins": (200, 400), "xp": 170, "rarity": "легендарное"},
{"id": "fish_peacock_bass", "name": "🐟 Павлин-басс", "min_level": 14, "weight": 11, "coins": (90, 180), "xp": 80, "rarity": "редкое"},
{"id": "fish_pacu", "name": "🐟 Паку", "min_level": 16, "weight": 10, "coins": (85, 170), "xp": 75, "rarity": "редкое"},
{"id": "fish_payara", "name": "🦈 Паяра (рыба-вампир)", "min_level": 22, "weight": 7, "coins": (140, 280), "xp": 120, "rarity": "легендарное"},

{"id": "fish_european_seabass", "name": "🐟 Европейский лаврак", "min_level": 11, "weight": 15, "coins": (65, 130), "xp": 60, "rarity": "редкое"},
{"id": "fish_atlantic_cod", "name": "🐟 Атлантическая треска", "min_level": 13, "weight": 14, "coins": (75, 150), "xp": 65, "rarity": "редкое"},
{"id": "fish_halibut_pacific", "name": "🐟 Тихоокеанский палтус", "min_level": 20, "weight": 9, "coins": (120, 240), "xp": 100, "rarity": "редкое"},
{"id": "fish_sailfish", "name": "🗡 Парусник", "min_level": 30, "weight": 4, "coins": (250, 500), "xp": 200, "rarity": "легендарное"},
{"id": "fish_marlin_blue", "name": "🗡 Голубой марлин", "min_level": 35, "weight": 3, "coins": (300, 600), "xp": 250, "rarity": "легендарное"},

{"id": "fish_wahoo", "name": "🐟 Ваху", "min_level": 18, "weight": 9, "coins": (110, 220), "xp": 95, "rarity": "редкое"},
{"id": "fish_king_mackerel", "name": "🐟 Королевская макрель", "min_level": 15, "weight": 11, "coins": (90, 180), "xp": 80, "rarity": "редкое"},
{"id": "fish_trevally_giant", "name": "🐟 Гигантский каранкс", "min_level": 27, "weight": 6, "coins": (190, 380), "xp": 160, "rarity": "легендарное"},
{"id": "fish_mahimahi_giant", "name": "🐟 Гигантский махи-махи", "min_level": 22, "weight": 7, "coins": (160, 320), "xp": 140, "rarity": "легендарное"},
{"id": "fish_ocean_sunfish", "name": "☀️ Рыба-луна", "min_level": 40, "weight": 2, "coins": (400, 800), "xp": 300, "rarity": "легендарное"},

{"id": "fish_megalodon", "name": "🦈 Мегалодон", "min_level": 35, "weight": 1, "coins": (800, 1500), "xp": 500, "rarity": "легендарное"},
{"id": "fish_leviathan", "name": "🐉 Левиафан", "min_level": 45, "weight": 1, "coins": (1200, 2500), "xp": 800, "rarity": "легендарное"},
{"id": "fish_kraken_tentacle", "name": "🦑 Щупальце Кракена", "min_level": 40, "weight": 2, "coins": (900, 1800), "xp": 600, "rarity": "легендарное"},
{"id": "fish_ancient_sturgeon", "name": "🐟 Древний осётр", "min_level": 32, "weight": 3, "coins": (500, 900), "xp": 350, "rarity": "легендарное"},
{"id": "fish_void_fish", "name": "🌌 Пустотная рыба", "min_level": 50, "weight": 1, "coins": (1500, 3000), "xp": 1000, "rarity": "легендарное"},

{"id": "fish_phantom_marlin", "name": "👻 Призрачный марлин", "min_level": 38, "weight": 2, "coins": (1000, 2000), "xp": 650, "rarity": "легендарное"},
{"id": "fish_dragonfish_abyssal", "name": "🐉 Глубинный драконохвост", "min_level": 42, "weight": 2, "coins": (1100, 2100), "xp": 700, "rarity": "легендарное"},
{"id": "fish_solar_whale", "name": "☀️ Солнечный кит", "min_level": 48, "weight": 1, "coins": (2000, 4000), "xp": 1200, "rarity": "легендарное"},
{"id": "fish_moon_eel", "name": "🌙 Лунный угорь", "min_level": 36, "weight": 2, "coins": (950, 1900), "xp": 620, "rarity": "легендарное"},
{"id": "fish_storm_swordfish", "name": "⛈ Штормовой рыба-меч", "min_level": 33, "weight": 3, "coins": (700, 1400), "xp": 500, "rarity": "легендарное"},

{"id": "fish_abyss_goliath", "name": "🌊 Голиаф бездны", "min_level": 44, "weight": 1, "coins": (1300, 2600), "xp": 900, "rarity": "легендарное"},
{"id": "fish_crystal_carp", "name": "💎 Хрустальный карп", "min_level": 31, "weight": 3, "coins": (600, 1200), "xp": 400, "rarity": "легендарное"},
{"id": "fish_time_salmon", "name": "⏳ Временной лосось", "min_level": 50, "weight": 1, "coins": (1800, 3600), "xp": 1100, "rarity": "легендарное"},
{"id": "fish_spectral_barracuda", "name": "👁 Спектральная барракуда", "min_level": 39, "weight": 2, "coins": (1000, 2100), "xp": 680, "rarity": "легендарное"},
{"id": "fish_emperor_koi", "name": "👑 Императорский кои", "min_level": 34, "weight": 2, "coins": (850, 1700), "xp": 550, "rarity": "легендарное"},

{"id": "fish_black_hole_fish", "name": "🕳 Рыба-чёрная дыра", "min_level": 50, "weight": 1, "coins": (2500, 5000), "xp": 1500, "rarity": "легендарное"},
{"id": "fish_thunder_whale_shark", "name": "⚡ Грозовой кит-акула", "min_level": 46, "weight": 1, "coins": (1600, 3200), "xp": 1000, "rarity": "легендарное"},
{"id": "fish_ancient_leviathan", "name": "🏛 Древний левиафан", "min_level": 50, "weight": 1, "coins": (3000, 6000), "xp": 2000, "rarity": "легендарное"},
{"id": "fish_eternal_eel", "name": "♾ Вечный угорь", "min_level": 47, "weight": 1, "coins": (1700, 3400), "xp": 1100, "rarity": "легендарное"},
{"id": "fish_godfish", "name": "🪶 Божественная рыба", "min_level": 50, "weight": 1, "coins": (5000, 10000), "xp": 3000, "rarity": "легендарное"},
]
    },

    "mine": {
        "name": "⛏️ Шахта",
        "good_action": "Добыто",
        "fail_action": "Ничего не добыто",
        "cooldown": 50,
        "level_field": "mine_level",
        "xp_field": "mine_xp",
        "fail_chance": 0.10,

        "loot": [
{"id": "mine_kamen", "name": "🪨 Камень", "min_level": 1, "weight": 80, "coins": (5, 10), "xp": 5, "rarity": "обычное"},
{"id": "mine_gravel", "name": "🪨 Гравий", "min_level": 1, "weight": 75, "coins": (4, 8), "xp": 4, "rarity": "обычное"},
{"id": "mine_clay", "name": "🟤 Глина", "min_level": 2, "weight": 60, "coins": (6, 12), "xp": 6, "rarity": "обычное"},
{"id": "mine_sandstone", "name": "🪨 Песчаник", "min_level": 2, "weight": 55, "coins": (7, 14), "xp": 7, "rarity": "обычное"},
{"id": "mine_limestone", "name": "🪨 Известняк", "min_level": 3, "weight": 45, "coins": (10, 18), "xp": 10, "rarity": "обычное"},

{"id": "mine_coal", "name": "⚫ Уголь", "min_level": 3, "weight": 40, "coins": (12, 25), "xp": 12, "rarity": "редкое"},
{"id": "mine_iron", "name": "⛏️ Железная руда", "min_level": 3, "weight": 30, "coins": (15, 25), "xp": 15, "rarity": "редкое"},
{"id": "mine_copper", "name": "🟠 Медь", "min_level": 4, "weight": 28, "coins": (18, 30), "xp": 18, "rarity": "редкое"},
{"id": "mine_tin", "name": "🪙 Олово", "min_level": 4, "weight": 25, "coins": (20, 35), "xp": 20, "rarity": "редкое"},
{"id": "mine_salt_rock", "name": "🧂 Каменная соль", "min_level": 5, "weight": 20, "coins": (25, 40), "xp": 22, "rarity": "редкое"},

{"id": "mine_quartz", "name": "💎 Кварц", "min_level": 5, "weight": 18, "coins": (30, 55), "xp": 30, "rarity": "редкое"},
{"id": "mine_obsidian", "name": "🖤 Обсидиан", "min_level": 6, "weight": 12, "coins": (40, 80), "xp": 40, "rarity": "редкое"},
{"id": "mine_granite", "name": "🪨 Гранит", "min_level": 6, "weight": 15, "coins": (35, 70), "xp": 35, "rarity": "редкое"},
{"id": "mine_basalt", "name": "🌑 Базальт", "min_level": 7, "weight": 10, "coins": (50, 90), "xp": 45, "rarity": "редкое"},
{"id": "mine_marble", "name": "🤍 Мрамор", "min_level": 7, "weight": 9, "coins": (60, 110), "xp": 50, "rarity": "редкое"},

{"id": "mine_silver_ore", "name": "🥈 Серебро", "min_level": 8, "weight": 8, "coins": (70, 130), "xp": 60, "rarity": "легендарное"},
{"id": "mine_gold_ore", "name": "🥇 Золото", "min_level": 9, "weight": 6, "coins": (100, 180), "xp": 80, "rarity": "легендарное"},
{"id": "mine_mythril", "name": "🔷 Мифрил", "min_level": 10, "weight": 4, "coins": (150, 300), "xp": 120, "rarity": "легендарное"},
{"id": "mine_adamantite", "name": "🟣 Адамантит", "min_level": 12, "weight": 3, "coins": (200, 400), "xp": 160, "rarity": "легендарное"},
{"id": "mine_void_crystal", "name": "🕳 Кристалл пустоты", "min_level": 15, "weight": 1, "coins": (500, 1000), "xp": 300, "rarity": "легендарное"},

{"id": "mine_coal", "name": "⚫ Уголь", "min_level": 15, "weight": 60, "coins": (20, 40), "xp": 20, "rarity": "редкое"},
{"id": "mine_iron_rich", "name": "⛏️ Богатая железная руда", "min_level": 16, "weight": 55, "coins": (25, 45), "xp": 25, "rarity": "редкое"},
{"id": "mine_copper_vein", "name": "🟠 Медная жила", "min_level": 16, "weight": 50, "coins": (28, 50), "xp": 28, "rarity": "редкое"},
{"id": "mine_tin_cluster", "name": "🪙 Оловянный кластер", "min_level": 17, "weight": 48, "coins": (30, 55), "xp": 30, "rarity": "редкое"},
{"id": "mine_salt_crystal", "name": "🧂 Соляной кристалл", "min_level": 18, "weight": 45, "coins": (35, 60), "xp": 32, "rarity": "редкое"},

{"id": "mine_quartz_vein", "name": "💎 Кварцевая жила", "min_level": 18, "weight": 40, "coins": (40, 75), "xp": 40, "rarity": "редкое"},
{"id": "mine_lapis", "name": "🔵 Лазурит", "min_level": 19, "weight": 35, "coins": (50, 90), "xp": 45, "rarity": "редкое"},
{"id": "mine_iron_dense", "name": "⛏️ Плотная железная руда", "min_level": 19, "weight": 38, "coins": (45, 80), "xp": 42, "rarity": "редкое"},
{"id": "mine_sulfur", "name": "🟡 Сера", "min_level": 20, "weight": 30, "coins": (55, 100), "xp": 50, "rarity": "редкое"},
{"id": "mine_clay_deep", "name": "🟤 Глубинная глина", "min_level": 20, "weight": 32, "coins": (50, 85), "xp": 45, "rarity": "редкое"},

{"id": "mine_granite_dense", "name": "🪨 Плотный гранит", "min_level": 21, "weight": 28, "coins": (60, 110), "xp": 55, "rarity": "редкое"},
{"id": "mine_marble_chunk", "name": "🤍 Мраморный блок", "min_level": 22, "weight": 25, "coins": (70, 120), "xp": 60, "rarity": "редкое"},
{"id": "mine_obsidian_shard", "name": "🖤 Обсидиановый осколок", "min_level": 23, "weight": 22, "coins": (80, 140), "xp": 70, "rarity": "редкое"},
{"id": "mine_basalt_column", "name": "🌑 Базальтовая колонна", "min_level": 24, "weight": 20, "coins": (90, 160), "xp": 75, "rarity": "редкое"},
{"id": "mine_silver_trace", "name": "🥈 Серебряный след", "min_level": 25, "weight": 18, "coins": (110, 180), "xp": 85, "rarity": "редкое"},

{"id": "mine_gold_nugget", "name": "🥇 Самородок золота", "min_level": 26, "weight": 12, "coins": (150, 250), "xp": 110, "rarity": "легендарное"},
{"id": "mine_mythril_fragment", "name": "🔷 Осколок мифрила", "min_level": 27, "weight": 10, "coins": (180, 300), "xp": 130, "rarity": "легендарное"},
{"id": "mine_adamantite_chunk", "name": "🟣 Кусок адамантита", "min_level": 28, "weight": 8, "coins": (220, 380), "xp": 150, "rarity": "легендарное"},
{"id": "mine_mana_stone", "name": "🔮 Мана-камень", "min_level": 29, "weight": 5, "coins": (300, 500), "xp": 200, "rarity": "легендарное"},
{"id": "mine_deep_core_crystal", "name": "🕳 Кристалл ядра глубин", "min_level": 30, "weight": 3, "coins": (400, 700), "xp": 260, "rarity": "легендарное"},
{"id": "mine_void_shard", "name": "🕳 Осколок пустоты", "min_level": 30, "weight": 6, "coins": (500, 900), "xp": 300, "rarity": "легендарное"},
    
{"id": "mine_star_iron", "name": "⭐ Звёздное железо", "min_level": 32, "weight": 5, "coins": (600, 1100), "xp": 350, "rarity": "легендарное"},
{"id": "mine_dragon_core", "name": "🐉 Ядро дракона", "min_level": 34, "weight": 4, "coins": (800, 1400), "xp": 450, "rarity": "легендарное"},
{"id": "mine_soul_crystal", "name": "👁 Кристалл души", "min_level": 36, "weight": 4, "coins": (900, 1600), "xp": 500, "rarity": "легендарное"},
{"id": "mine_abyss_ore", "name": "🌊 Руда бездны", "min_level": 38, "weight": 3, "coins": (1100, 1900), "xp": 600, "rarity": "легендарное"},

{"id": "mine_eternal_gold", "name": "🥇 Вечное золото", "min_level": 40, "weight": 3, "coins": (1300, 2200), "xp": 700, "rarity": "легендарное"},
{"id": "mine_gravity_stone", "name": "🪨 Гравитационный камень", "min_level": 42, "weight": 2, "coins": (1500, 2600), "xp": 800, "rarity": "легендарное"},
{"id": "mine_time_crystal", "name": "⏳ Кристалл времени", "min_level": 45, "weight": 2, "coins": (1800, 3000), "xp": 950, "rarity": "легендарное"},
{"id": "mine_phantom_iron", "name": "👻 Фантомное железо", "min_level": 48, "weight": 2, "coins": (2000, 3400), "xp": 1100, "rarity": "легендарное"},
{"id": "mine_singularity_core", "name": "⚫ Ядро сингулярности", "min_level": 50, "weight": 1, "coins": (2500, 4000), "xp": 1400, "rarity": "легендарное"},

{"id": "mine_cosmic_diamond", "name": "💎 Космический алмаз", "min_level": 55, "weight": 1, "coins": (3000, 5000), "xp": 1600, "rarity": "легендарное"},
{"id": "mine_ancient_bedrock", "name": "🏛 Древний коренной камень", "min_level": 58, "weight": 1, "coins": (3200, 5500), "xp": 1700, "rarity": "легендарное"},
{"id": "mine_hellstone", "name": "🔥 Адский камень", "min_level": 60, "weight": 1, "coins": (3500, 6000), "xp": 1900, "rarity": "легендарное"},
{"id": "mine_frost_crystal", "name": "❄️ Ледяной кристалл", "min_level": 63, "weight": 1, "coins": (3800, 6500), "xp": 2000, "rarity": "легендарное"},
{"id": "mine_light_core", "name": "☀️ Ядро света", "min_level": 66, "weight": 1, "coins": (4200, 7000), "xp": 2200, "rarity": "легендарное"},

{"id": "mine_dark_matter", "name": "🌌 Тёмная материя", "min_level": 70, "weight": 1, "coins": (5000, 8500), "xp": 2600, "rarity": "легендарное"},
{"id": "mine_world_seed", "name": "🌱 Семя мира", "min_level": 75, "weight": 1, "coins": (6000, 10000), "xp": 3000, "rarity": "легендарное"},
{"id": "mine_reality_fragment", "name": "🧩 Фрагмент реальности", "min_level": 80, "weight": 1, "coins": (7000, 12000), "xp": 3400, "rarity": "легендарное"},
{"id": "mine_god_ore", "name": "🪶 Божественная руда", "min_level": 90, "weight": 1, "coins": (9000, 15000), "xp": 4000, "rarity": "легендарное"},
{"id": "mine_true_void", "name": "🕳 Истинная пустота", "min_level": 100, "weight": 1, "coins": (12000, 20000), "xp": 5000, "rarity": "легендарное"}
        ]
    }   
}

STORAGE_ITEMS_INDEX = {}
def build_item_index():
    STORAGE_ITEMS_INDEX.clear()

    for activity_name, activity in ACTIVITIES.items():
        for item in activity["loot"]:
            STORAGE_ITEMS_INDEX[item["id"]] = {
                "activity": activity_name,
                **item
            }

xp_potion_text = "Бустит получение XP\nМожет сломаться"
coin_potion_text = "Бустит получение денег\nМожет сломаться"
trade_potion_text = "Рандомно бустит денеги\nШанс проиграть деньги\nМожет сломаться"
SHOP = {    
    "xp_potion_f": {
        "name": "🧪 Зелье опыта (подделка)",
        "effect_name": xp_potion_text,
        "price": 25,
        "type": "расходник, баф",
        "effect": {
            "xp_buff": 1.5,
            "vanish_chance": 0.40
        },
    },
    "coin_potion_f": {
        "name": "🧪 Зелье денег (подделка)",
        "effect_name": coin_potion_text,
        "price": 50,
        "type": "расходник, баф",
        "effect": {
            "coin_buff": 1.5,
            "vanish_chance": 0.40
        },
    },
    "xp_potion_e": {
        "name": "🧪 Зелье опыта E",
        "effect_name": xp_potion_text,
        "price": 200,
        "type": "расходник, баф",
        "effect": {
            "xp_buff": 2.0,
            "vanish_chance": 0.20
        },
    },
    "coin_potion_e": {
        "name": "🧪 Зелье денег E",
        "effect_name": coin_potion_text,
        "price": 500,
        "type": "расходник, баф",
        "effect": {
            "coin_buff": 2.0,
            "vanish_chance": 0.25
        },
    },
    "xp_potion_d": {
        "name": "🧪 Зелье опыта D",
        "effect_name": xp_potion_text,
        "price": 600,
        "type": "расходник, баф",
        "effect": {
            "xp_buff": 3.5,
            "vanish_chance": 0.025
        },
    },
    "coin_potion_d": {
        "name": "🧪 Зелье денег D",
        "effect_name": coin_potion_text,
        "price": 500,
        "type": "расходник, баф",
        "effect": {
            "coin_buff": 5.0,
            "vanish_chance": 0.5
        },
    },
    "xp_potion_c": {
        "name": "🧪 Зелье опыта C",
        "effect_name": xp_potion_text,
        "price": 1000,
        "type": "расходник, баф",
        "effect": {
            "xp_buff": 4.5,
            "vanish_chance": 0.025
        },
    },
    "coin_potion_c": {
        "name": "🧪 Зелье денег C",
        "effect_name": coin_potion_text,
        "price": 2000,
        "type": "расходник, баф",
        "effect": {
            "coin_buff": 4.5,
            "vanish_chance": 0.025
        },
    },
    "xp_potion_b": {
        "name": "🧪 Зелье опыта B",
        "effect_name": xp_potion_text,
        "price": 5000,
        "type": "расходник, баф",
        "effect": {
            "xp_buff": 6.7,
            "vanish_chance": 0.17
        },
    },
    "coin_potion_b": {
        "name": "🧪 Зелье денег B",
        "effect_name": coin_potion_text,
        "price": 18000,
        "type": "расходник, баф",
        "effect": {
            "coin_buff": 5.0,
            "vanish_chance": 0.05
        },
    },
    "xp_potion_a": {
        "name": "🧪 Зелье опыта A",
        "effect_name": xp_potion_text,
        "price": 50000,
        "type": "расходник, баф",
        "effect": {
            "xp_buff": 6.0,
            "vanish_chance": 0.009
        },
    },
    "coin_potion_a": {
        "name": "🧪 Зелье денег A",
        "effect_name": coin_potion_text,
        "price": 115000,
        "type": "расходник, баф",
        "effect": {
            "coin_buff": 7.0,
            "vanish_chance": 0.009
        },
    },
    "xp_potion_s": {
        "name": "🧪 Зелье опыта S",
        "effect_name": xp_potion_text,
        "price": 100000,
        "type": "расходник, баф",
        "effect": {
            "xp_buff": 8.5,
            "vanish_chance": 0.005
        },
    },
    "coin_potion_s": {
        "name": "🧪 Зелье денег S",
        "effect_name": coin_potion_text,
        "price": 600000,
        "type": "расходник, баф",
        "effect": {
            "coin_buff": 9.5,
            "vanish_chance": 0.001
        },
    },
    "random_potion_x": {
        "name": "🧪 Радиактивное зелье",
        "effect_name": "Эффекты неизвестны\nМожет сломаться",
        "price": 1000000,
        "type": "расходник, баф",
        "effect": {
            "random_buff": 25.0,
            "vanish_chance": 0.001
        },
    }, 
    "collectable_1": {
        "name": "👤 Стас",
        "effect_name": "Талисман\nНе имет эффектов\nМожет сломаться",
        "price": 1,
        "type": "расходник, талисман",
        "effect": {
            "aura_buff": 1.25,
            "vanish_chance": 0.00001
        },
    },
    "trade_b": {
        "name": "🍢 Сделка B",
        "effect_name": trade_potion_text,
        "price": 1,
        "type": "расходник, казино",
        "effect": {
            "negative_coin_chance": 0.5,
            "vanish_chance": 0.0001
        },
    },
    "trade_a": {
        "name": "🍢 Сделка A",
        "effect_name": trade_potion_text,
        "price": 1,
        "type": "расходник, казино",
        "effect": {
            "coin_buff": 10.0,
            "negative_coin_chance": 0.3,
            "vanish_chance": 0.025
        },
    },
    "trade_x": {
        "name": "🍢 Сделка S",
        "effect_name": trade_potion_text,
        "price": 1,
        "type": "расходник, казино",
        "effect": {
            "coin_buff": 5.0,
            "negative_coin_chance": 0.25,
            "vanish_chance": 0.005
        },
    },
    "trade_ss": {
        "name": "🍢 Сделка S+",
        "effect_name": trade_potion_text,
        "price": 1,
        "type": "расходник, казино",
        "effect": {
            "coin_buff": 10.0,
            "negative_coin_chance": 0.2,
            "vanish_chance": 0.001
        },
    },
    "gamble_coin_1": {
        "name": "🌶 Гемблинг перец I",
        "effect_name": "Рандомный множитель денег\nМожно проиграть все\nМожет сломаться",
        "price": 50,
        "type": "расходник, казино",
        "effect": {
            "coin_multiplier_random": 10.0,
            "negative_coin_chance": 0.30,
            "vanish_chance": 0.01
        },
    },
    "gamble_coin_2": {
        "name": "🌶 Гемблинг перец II",
        "effect_name": "Рандомный множитель денег\nМожно проиграть все\nМожет сломаться",
        "price": 1000,
        "type": "расходник, казино",
        "effect": {
            "coin_multiplier_random": 30.0,
            "negative_coin_chance": 0.50,
            "vanish_chance": 0.05
        },
    },
    "gamble_xp_1": {
        "name": "🥖 Гемблинг батон I",
        "effect_name": "Рандомный множитель XP\nМожет сломаться",
        "price": 100,
        "type": "расходник, казино",
        "effect": {
            "xp_multiplier_random": 3.0,
            "negative_coin_chance": 0.10,
            "vanish_chance": 0.10
        },
    },
    "gamble_xp_2": {
        "name": "🥖 Гемблинг батон II",
        "effect_name": "Рандомный множитель XP\nМожет сломаться",
        "price": 10000,
        "type": "расходник, казино",
        "effect": {
            "xp_multiplier_random": 5.0,
            "negative_coin_chance": 0.50,
            "vanish_chance": 0.05
        },
    },
    "xp_trade": {
        "name": "🩸 Трейд ХР",
        "effect_name": "Множитель XP\nТратит деньги\nМожет сломаться",
        "price": 500,
        "type": "казино, обмен, расходник",
        "effect": {
            "xp_multiplier_random": 15.0,
            "coin_multiplier_random": 15.0,
            "negative_coin_chance": 1.00,
            "vanish_chance": 0.0001
        },
    },
    "item_trade_fish": {
        "name": "💎 Продажа предметов (рыба)",
        "effect_name": "Баф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 1000,
        "type": "расходник, торговля",
        "effect": {
            "trade_type": "fish",
            "trade_multiplier": 10,
            "vanish_chance": 0.05
        },
    },
    "item_trade_mine": {
        "name": "💎 Продажа предметов (шахта)",
        "effect_name": "Баф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 1000,
        "type": "расходник, торговля",
        "effect": {
            "trade_type": "mine",
            "trade_multiplier": 10,
            "vanish_chance": 0.05
        },
    }
}


UPGRADES = {
    "fish_tool": {
        "name": "🎣 Удочка",
        "effect_name": "Немного уменьшает таймаут",
        "field": "fish_tool_level",
        "base_price": 100,
        "price_mult": 1.3,
    },

    "mine_tool": {
        "name": "⛏️ Кирка",
        "effect_name": "Немного уменьшает таймаут",
        "field": "mine_tool_level",
        "base_price": 100,
        "price_mult": 1.3,
    },

    "fish_luck": {
        "name": "🍀 Удача рыбалки",
        "effect_name": "Немного увеличивает удачу",
        "field": "fish_luck_level",
        "base_price": 250,
        "price_mult": 2.5,
    },

    "mine_luck": {
        "name": "🍀 Удача шахты",
        "effect_name": "Немного увеличивает удачу",
        "field": "mine_luck_level",
        "base_price": 250,
        "price_mult": 2.5,
    },
}

RARITY_MULTIPLIER = {
    "обычное": 1.0,
    "редкое": 1.2,
    "очень редкое": 1.5,
    "эпическое": 2.0,
    "легендарное": 3.5
}

RARITY_EMOJI = {
    "обычное": "⚪",
    "редкое": "🟢",
    "очень редкое": "🔵",
    "эпическое": "🟣",
    "легендарное": "🟡"
}

def apply_slot(user_id, value, best_item, buff_key, log, slot_name, is_random=False):
    if not best_item:
        return value, log

    item_id = best_item["id"]
    effect = best_item["effect"]

    # сломался предмет
    if random.random() < effect.get("vanish_chance", 0):
        remove_item(user_id, item_id, 1)

        log["broken"].append(item_id)
        log["selected"][slot_name] = "BROKEN"
        return value, log

    # обычный множитель
    if not is_random:
        value = int(value * effect[buff_key])
    else:
        # random multiplier
        value = int(value * random.uniform(1.0, effect[buff_key]))

    log["selected"][slot_name] = item_id
    return value, log

def apply_effects(user_id: int, base, context):
    inventory = get_inventory(user_id)

    best = {
        "xp_buff": None,
        "xp_random": None,
        "coin_buff": None,
        "coin_random": None,
        "trade": None
    }

    log = {
        "base": base.copy(),
        "selected": {},
        "broken": [],
        "steps": [],
        "final": {}
    }

    xp = base["xp"]
    coins = base["coins"]

    # 1. выбор лучших предметов по слотам
    for item_id, amount in inventory:
        item = SHOP.get(item_id)
        if not item:
            continue

        effect = item.get("effect", {})

        # XP buff
        if "xp_buff" in effect:
            if (best["xp_buff"] is None or
                effect["xp_buff"] > best["xp_buff"]["effect"]["xp_buff"]):
                best["xp_buff"] = {"id": item_id, "effect": effect}

        # XP random
        if "xp_multiplier_random" in effect:
            if (best["xp_random"] is None or
                effect["xp_multiplier_random"] > best["xp_random"]["effect"]["xp_multiplier_random"]):
                best["xp_random"] = {"id": item_id, "effect": effect}

        # COIN buff
        if "coin_buff" in effect:
            if (best["coin_buff"] is None or
                effect["coin_buff"] > best["coin_buff"]["effect"]["coin_buff"]):
                best["coin_buff"] = {"id": item_id, "effect": effect}

        # COIN random
        if "coin_multiplier_random" in effect:
            if (best["coin_random"] is None or
                effect["coin_multiplier_random"] > best["coin_random"]["effect"]["coin_multiplier_random"]):
                best["coin_random"] = {"id": item_id, "effect": effect}

        # TRADE
        if "negative_coin_chance" in effect:
            if (best["trade"] is None or
                effect["negative_coin_chance"] > best["trade"]["effect"]["negative_coin_chance"]):
                best["trade"] = {"id": item_id, "effect": effect}

    # 2. XP slots
    xp, log = apply_slot(user_id, xp, best["xp_buff"], "xp_buff", log, "xp_buff")
    xp, log = apply_slot(user_id, xp, best["xp_random"], "xp_multiplier_random", log, "xp_random", is_random=True)

    # 3. COINS slots
    coins, log = apply_slot(user_id, coins, best["coin_buff"], "coin_buff", log, "coin_buff")
    coins, log = apply_slot(user_id, coins, best["coin_random"], "coin_multiplier_random", log, "coin_random", is_random=True)

    # 4. TRADE
    if best["trade"]:
        item_id = best["trade"]["id"]
        effect = best["trade"]["effect"]

        if random.random() < effect["negative_coin_chance"]:
            coins = -coins

            log["steps"].append({
                "type": "trade_penalty",
                "item": item_id,
                "lost_coins": coins
            })

        log["selected"]["trade"] = item_id

    log["final"] = {
        "xp": xp,
        "coins": coins
    }

    return xp, coins, log

def format_buffs_log(log):
    lines = ["📊 Бафы предметов\n"]

    if not log["steps"]:
        return "📊 Бафов нет"

    for step in log["steps"]:
        lines.append(
            f"🎒 {step['item']} x{step['amount']}"
        )
        lines.append(
            f"   до: XP {step['before']['xp']} | 💰 {step['before']['coins']}"
        )

        if "after_xp" in step:
            lines.append(f"   после XP: {step['after_xp']}")

        if "after_coins" in step:
            lines.append(f"   после 💰: {step['after_coins']}")

        lines.append("")

    lines.append(
        f"⚙️ ИТОГО: +{log['final']['xp']} XP / +{log['final']['coins']} 💰"
    )

    return "\n".join(lines)

def get_last_activity(user_id: int, activity: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    field = get_last_field(activity)

    cur.execute(
        f"""
        SELECT {field}
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    )

    row = cur.fetchone()
    conn.close()

    if not row:
        return 0

    return row[0]

def set_last_activity(user_id: int, activity: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    field = f"last_{activity}"
    now = int(time.time())

    cur.execute(
        f"""
        UPDATE users
        SET {field} = ?
        WHERE telegram_id = ?
        """,
        (now, user_id)
    )

    conn.commit()
    conn.close()

def get_upgrade_price(upgrade_id, level):
    data = UPGRADES[upgrade_id]

    return int(
        data["base_price"] *
        (data["price_mult"] ** (level - 1))
    )

def get_available_loot(activity, level):
    return [
        item for item in ACTIVITIES[activity]["loot"]
        if item["min_level"] <= level
    ]

def init_db():
    conn = sqlite3.connect(DB_PATH)

    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        telegram_name TEXT,

        coins INTEGER NOT NULL DEFAULT 0,

        fish_level INTEGER NOT NULL DEFAULT 1,
        mine_level INTEGER NOT NULL DEFAULT 1,

        fish_xp INTEGER NOT NULL DEFAULT 0,
        mine_xp INTEGER NOT NULL DEFAULT 0,

        last_fish INTEGER NOT NULL DEFAULT 0,
        last_mine INTEGER NOT NULL DEFAULT 0,
                
        fish_tool_level INTEGER NOT NULL DEFAULT 1,
        mine_tool_level INTEGER NOT NULL DEFAULT 1,

        fish_luck_level INTEGER NOT NULL DEFAULT 1,
        mine_luck_level INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS inventory_items (
        telegram_id INTEGER NOT NULL,
        item_id TEXT NOT NULL,
        amount INTEGER NOT NULL DEFAULT 0,

        PRIMARY KEY (telegram_id, item_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS storage_items (
        telegram_id INTEGER NOT NULL,
        item_id TEXT NOT NULL,
        amount INTEGER NOT NULL DEFAULT 0,

        PRIMARY KEY (telegram_id, item_id)
    )
    """)

    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(DB_PATH)


def ensure_user(user_id: int, user_name: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users
    (telegram_id, telegram_name, coins)
    VALUES (?, ?, 0)
    """, (user_id, user_name))

    cur.execute("""
    UPDATE users
    SET telegram_name = ?
    WHERE telegram_id = ?
    """, (user_name, user_id))

    conn.commit()
    conn.close()

def level_multiplier(level):
    return 1 + (level * 0.05)

def add_coins(user_id: int, amount: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET coins = coins + ?
    WHERE telegram_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()


def get_balance(user_id: int) -> int:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT coins
    FROM users
    WHERE telegram_id = ?
    """, (user_id,))

    row = cur.fetchone()

    conn.close()

    return row[0] if row else 0

def add_storage_item(user_id: int, item_id: str, amount: int = 1):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO storage_items (telegram_id, item_id, amount)
    VALUES (?, ?, ?)
    ON CONFLICT(telegram_id, item_id)
    DO UPDATE SET amount = amount + excluded.amount
    """, (user_id, item_id, amount))

    conn.commit()
    conn.close()

def add_inventory_item(user_id: int, item_id: str, amount: int = 1):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO inventory_items (telegram_id, item_id, amount)
    VALUES (?, ?, ?)
    ON CONFLICT(telegram_id, item_id)
    DO UPDATE SET amount = amount + excluded.amount
    """, (user_id, item_id, amount))

    conn.commit()
    conn.close()

def buy_item(user_id: int, item_id: str):
    item = SHOP.get(item_id)

    if not item:
        return False, "❌ Предмет не найден"

    balance = get_balance(user_id)

    if balance < item["price"]:
        return False, "💸 Не хватает денег"

    add_coins(user_id, -item["price"])
    add_inventory_item(user_id, item_id)

    return True, f"✅ Куплено\n(добавлено в инвентарь)"

def remove_item(user_id: int, item_id: str, amount: int = 1):
    conn = get_conn()
    cur = conn.cursor()

    # уменьшаем количество
    cur.execute("""
        UPDATE inventory_items
        SET amount = amount - ?
        WHERE telegram_id = ? AND item_id = ?
    """, (amount, user_id, item_id))

    # удаляем если 0
    cur.execute("""
        DELETE FROM inventory_items
        WHERE telegram_id = ? AND item_id = ?
          AND amount <= 0
    """, (user_id, item_id))

    conn.commit()
    conn.close()

async def sell_inventory_all(query):
    
    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    items = get_inventory(user_id)
    balance = get_balance(user_id)

    text = f"<b>{user_name}</b>\n"

    if not items:
        text += f"<code>- баланс: {balance}</code>\n\n"
        text += "🎒 <b>Инвентарь пуст.</b>"        
  
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(user_id)
        )
        return

    total_coins = 0

    for item_id, amount in items:

        item = SHOP.get(item_id)

        if not item:
            continue

        price = item.get("price", "2")
        avg_price = price // 2

        total_coins += avg_price * amount

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM inventory_items WHERE telegram_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    add_coins(user_id, total_coins)
    
    text += f"<code>- баланс: {balance + total_coins}</code>\n\n"
    text += f"<b>Продано всe.</b>\n"
    text += f"<code>- профит: {total_coins} денег</code>"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_goback_keyboard(user_id)
    )

async def sell_inventory_duplicates(query):
    
    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    items = get_inventory(user_id)
    balance = get_balance(user_id)

    text = f"<b>{user_name}</b>\n"

    if not items:
        text += f"<code>- баланс: {balance}</code>\n\n"
        text += "🎒 <b>Инвентарь пуст.</b>"
  
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(user_id)
        )
        return

    total_coins = 0

    conn = get_conn()
    cur = conn.cursor()

    for item_id, amount in items:

        if amount <= 1:
            continue

        item = SHOP.get(item_id)
        if not item:
            continue

        price = item.get("price", "2")
        avg_price = price // 2

        duplicates = amount - 1

        total_coins += avg_price * duplicates

        cur.execute("""
            UPDATE inventory_items
            SET amount = 1
            WHERE telegram_id = ? AND item_id = ?
        """, (user_id, item_id))

    conn.commit()
    conn.close()

    add_coins(user_id, total_coins)
    
    text += f"<code>- баланс: {balance + total_coins}</code>\n\n"
    text += f"<b>Дубликаты проданы.</b>\n"
    text += f"<code>- профит: {total_coins} денег</code>"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_goback_keyboard(user_id)
    )

async def sell_storage_all(query):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    items = get_storage(user_id)
    balance = get_balance(user_id)

    text = f"<b>{user_name}</b>\n"

    if not items:
        text += f"<code>- баланс: {balance}</code>\n\n"
        text += "🕳 <b>Хранилище пустое.</b>"

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(user_id)
        )
        return

    total_coins = 0
    used_trade_items = set()

    conn = get_conn()
    cur = conn.cursor()

    for item_id, amount in items:

        item = STORAGE_ITEMS_INDEX.get(item_id)
        if not item:
            continue

        price = item.get("coins", (0, 0))[0]
        avg_price = price // 2

        final_price = apply_trade_multiplier(
            user_id,
            item,
            avg_price,
            used_trade_items
        )

        total_coins += final_price * amount

    broken_items = process_trade_item_breaks(
        user_id,
        used_trade_items
    )

    cur.execute(
        "DELETE FROM storage_items WHERE telegram_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    add_coins(user_id, total_coins)

    text += f"<code>- баланс: {balance + total_coins}</code>\n\n"
    text += "<b>Продано все.</b>\n"
    text += f"<code>- профит: {total_coins} денег</code>"

    if broken_items:
        text += "\n\n💥 <b>Сломались:</b>\n"

        for item_id in broken_items:
            item = SHOP.get(item_id)

            if item:
                text += f"<code>- {item['name']}</code>\n"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_goback_keyboard(user_id)
    )

async def sell_storage_duplicates(query):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    items = get_storage(user_id)
    balance = get_balance(user_id)

    text = f"<b>{user_name}</b>\n"

    if not items:
        text += f"<code>- баланс: {balance}</code>\n\n"
        text += "🕳 <b>Хранилище пустое.</b>"

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(user_id)
        )
        return

    total_coins = 0
    used_trade_items = set()

    conn = get_conn()
    cur = conn.cursor()

    for item_id, amount in items:

        if amount <= 1:
            continue

        item = STORAGE_ITEMS_INDEX.get(item_id)
        if not item:
            continue

        price = item.get("coins", (0, 0))[0]
        avg_price = price // 2

        final_price = apply_trade_multiplier(
            user_id,
            item,
            avg_price,
            used_trade_items
        )

        duplicates = amount - 1

        total_coins += final_price * duplicates

        cur.execute("""
            UPDATE storage_items
            SET amount = 1
            WHERE telegram_id = ? AND item_id = ?
        """, (user_id, item_id))

    broken_items = process_trade_item_breaks(
        user_id,
        used_trade_items
    )

    conn.commit()
    conn.close()

    add_coins(user_id, total_coins)

    text += f"<code>- баланс: {balance + total_coins}</code>\n\n"
    text += "<b>Дубликаты проданы.</b>\n"
    text += f"<code>- профит: {total_coins} денег</code>"

    if broken_items:
        text += "\n\n💥 <b>Сломались:</b>\n"

        for item_id in broken_items:
            item = SHOP.get(item_id)

            if item:
                text += f"<code>- {item['name']}</code>\n"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_goback_keyboard(user_id)
    )
    
def apply_trade_multiplier(user_id, item, base_price, used_trade_items):
    final_price = base_price

    activity = item.get("activity")

    if activity not in ("fish", "mine"):
        return final_price

    trade_item = get_best_trade_item(user_id, activity)

    if not trade_item:
        return final_price

    final_price *= trade_item["mult"]

    used_trade_items.add(trade_item["id"])

    return final_price

def process_trade_item_breaks(user_id, used_trade_items):
    broken = []

    for item_id in used_trade_items:

        item = SHOP.get(item_id)
        if not item:
            continue

        vanish = item.get("effect", {}).get("vanish_chance", 0)

        if random.random() < vanish:
            remove_item(user_id, item_id, 1)
            broken.append(item_id)

    return broken

def get_best_trade_item(user_id, trade_type):
    inventory = get_inventory(user_id)

    best = None

    for item_id, amount in inventory:
        item = SHOP.get(item_id)
        if not item:
            continue

        effect = item.get("effect", {})

        if effect.get("trade_type") != trade_type:
            continue

        mult = effect.get("trade_multiplier", 1)

        if best is None or mult > best["mult"]:
            best = {
                "id": item_id,
                "mult": mult,
                "effect": effect
            }

    return best

def buy_upgrade(user_id: int, upgrade_id: str):

    upgrade = UPGRADES.get(upgrade_id)

    if not upgrade:
        return False, "❌ Апгрейд не найден"

    level = get_user_field(
        user_id,
        upgrade["field"],
        0
    )

    if "tool" in upgrade_id:
        level = max(level, 1)

    next_level = level + 1

    price = get_upgrade_price(
        upgrade_id,
        next_level
    )

    balance = get_balance(user_id)

    if balance < price:
        return False, "💸 Не хватает денег"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        UPDATE users
        SET
            coins = coins - ?,
            {upgrade['field']} = {upgrade['field']} + 1
        WHERE telegram_id = ?
        """,
        (
            price,
            user_id
        )
    )

    conn.commit()
    conn.close()

    return True, (
        f"✅ Успешно улучшено"
    )

def get_upgrade_info(user_id: int, upgrade_id: str):

    upgrade = UPGRADES.get(upgrade_id)

    if not upgrade:
        return None

    level = get_upgrade_level(
        user_id,
        upgrade_id
    )

    next_price = get_upgrade_price(
        upgrade_id,
        level + 1
    )

    return {
        "id": upgrade_id,
        "name": upgrade["name"],
        "level": level,
        "next_price": next_price,
    }

def add_xp(user_id: int, activity: str, xp: int):

    level_field = ACTIVITIES[activity]["level_field"]
    xp_field = ACTIVITIES[activity]["xp_field"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT {level_field}, {xp_field}
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    if not row:
        conn.close()
        return

    level, current_xp = row

    current_xp += xp

    while current_xp >= level * 100:
        current_xp -= level * 100
        level += 1

    cur.execute(
        f"""
        UPDATE users
        SET
            {level_field} = ?,
            {xp_field} = ?
        WHERE telegram_id = ?
        """,
        (
            level,
            current_xp,
            user_id
        )
    )

    conn.commit()
    conn.close()

def get_inventory(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT item_id, amount
    FROM inventory_items
    WHERE telegram_id = ?
    ORDER BY amount DESC
    """, (user_id,))

    rows = cur.fetchall()

    conn.close()

    return rows

def get_storage(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    SELECT item_id, amount
    FROM storage_items
    WHERE telegram_id = ?
    ORDER BY amount DESC
    """, (user_id,))

    rows = cur.fetchall()

    conn.close()

    return rows

def get_progress(user_id: int, activity: str):

    level_field = ACTIVITIES[activity]["level_field"]
    xp_field = ACTIVITIES[activity]["xp_field"]

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT {level_field}, {xp_field}
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    if not row:
        return 1, 0, 100

    level, xp = row

    return level, xp, level * 100

def apply_tool_luck(tool_level: int, loot_table: list):

    if tool_level <= 1 or not loot_table:
        return [(item, item["weight"]) for item in loot_table], 1.0

    luck_power = 1 + (tool_level - 1) * 0.06

    modified_table = []

    for item in loot_table:
        weight = item["weight"]
        rarity = item.get("rarity", "обычное")

        if rarity == "редкое":
            weight *= (1 + (luck_power - 1) * 0.8)
        elif rarity == "очень редкое":
            weight *= (1 + (luck_power - 1) * 1.2)
        elif rarity == "эпическое":
            weight *= (1 + (luck_power - 1) * 1.6)
        elif rarity == "легендарное":
            weight *= (1 + (luck_power - 1) * 2.2)

        modified_table.append((item, int(weight)))

    fail_modifier = max(1 - (tool_level - 1) * 0.04, 0.6)

    return modified_table, fail_modifier

def roll_loot(
    activity_name: str,
    level: int,
    luck_level: int,
    tool_level: int
):
    loot_table = get_available_loot(activity_name, level)

    if not loot_table:
        return None, None, 0, 0, "none"

    modified_table, tool_fail_mod = apply_tool_luck(
        tool_level,
        loot_table
    )

    weighted_loot = []

    for item, base_weight in modified_table:

        rarity = item.get("rarity", "обычное")

        luck_bonus = 1 + luck_level * {
            "редкое": 0.05,
            "очень редкое": 0.08,
            "эпическое": 0.12,
            "легендарное": 0.18
        }.get(rarity, 0)

        weight = max(1, int(base_weight * luck_bonus))

        weighted_loot.append((item, weight))

    base_fail = ACTIVITIES[activity_name].get("fail_chance", 0.10)

    fail_chance = base_fail * (1 - level * 0.02)

    fail_chance *= max(1 - luck_level * 0.03, 0.25)

    fail_chance *= tool_fail_mod

    fail_chance = max(fail_chance, 0.01)

    if random.random() < fail_chance:
        return None, None, 0, 0, "fail"

    # 4. roll
    total_weight = sum(w for _, w in weighted_loot)
    roll = random.randint(1, total_weight)

    current = 0

    for item, weight in weighted_loot:
        current += weight
        if roll <= current:
            coins = random.randint(*item["coins"])
            xp = item["xp"]
            return item["id"], item["name"], coins, xp, item["rarity"]

    item = random.choice(loot_table)
    return item["id"], item["name"], random.randint(*item["coins"]), item["xp"], item["rarity"]

def get_last_field(activity: str) -> str:
    return f"last_{activity}"

async def do_activity(query, activity_name):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    now = int(time.time())
    last = get_last_activity(user_id, activity_name)


    tool_level = get_tool_level(
        user_id,
        activity_name
    )

    cooldown_mult = max(
        1 - (tool_level - 1) * 0.05,
        0.30
    )

    cooldown = int(
        ACTIVITIES[activity_name]["cooldown"] *
        cooldown_mult
    )


    if now - last < cooldown:        
        activity_title_text = ACTIVITIES[activity_name]["name"]
        text = (
            f"<b>{user_name}</b>\n\n"
            f"{activity_title_text}\n"
            f"<code>- жди {cooldown - (now - last)} сек.</code>\n"
            f"<code>- или улучши 🧬</code>\n"
        )
        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_actions_keyboard(user_id)
        )
        return

    set_last_activity(user_id, activity_name)

    level, _, _ = get_progress(
        user_id,
        activity_name
    )

    balance = get_balance(user_id)
    
    luck_level = get_luck_level(
        user_id,
        activity_name
    )

    item_id, item_name, coins, xp, rarity = roll_loot(
        activity_name,
        level,
        luck_level,
        tool_level
    )

    activity_fail_action_text = ACTIVITIES[activity_name]["fail_action"]

    if rarity == "fail":
        level, current_xp, needed_xp = get_progress(
            user_id,
            activity_name
        )
        
        text = (
            f"<b>{user_name}</b> <code>(lvl. {level})</code>\n"
            f"<code>- левел ап: {current_xp}/{needed_xp}</code>\n"
            f"<code>- баланс: {balance}</code>\n"            
            f"\n"
            # f"{activity_title_text}\n"        
            # f"\n"
            f"{activity_fail_action_text}\n"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_actions_keyboard(user_id)
        )
        return
    
    mult = RARITY_MULTIPLIER.get(rarity, 1.0)

    coins = int(coins * level_multiplier(level) * mult)
    xp = int(xp * level_multiplier(level) * mult)

    add_storage_item(
        user_id,
        item_id=item_id,
        amount=1
    )

    base = {
        "xp": xp,
        "coins": coins
    }

    final_xp, final_coins, log = apply_effects(user_id, base, {
        "activity": activity_name
    })

    # print(json.dumps(log, indent=4, ensure_ascii=False))

    add_coins(user_id, final_coins)
    add_xp(user_id, activity_name, final_xp)

    level, current_xp, needed_xp = get_progress(
        user_id,
        activity_name
    )
    
    raity_emoji = RARITY_EMOJI.get(rarity, "⚪")    
    activity_good_action_text = ACTIVITIES[activity_name]["good_action"]

    broken_items_text = ""

    if log["broken"]:
        broken_names = []

        for item_id in log["broken"]:
            item = SHOP.get(item_id)
            broken_names.append(item["name"] if item else item_id)

        broken_items_text = (
            "\n\n💥 Сломались предметы:\n" +
            "\n".join(f"<code>- {name}</code>" for name in broken_names)
        )

    text = (
        f"<b>{user_name}</b> <code>(lvl. {level})</code>\n"
        f"<code>- баланс: {balance + coins}</code>\n"
        f"<code>- левел ап: {current_xp}/{needed_xp}</code>\n"
        f"\n"        
        # f"{activity_title_text}\n"        
        # f"\n"
        f"{activity_good_action_text}: <b>{item_name}</b>\n"
        f"<code>- {raity_emoji} редкость: {rarity}</code>\n"
        f"<code>- 🪙 деньги: {final_coins} </code>\n"
        f"<code>- ⭐️ опыт: {final_xp} XP</code>" 
        f"{broken_items_text}"               
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=get_actions_keyboard(user_id)
    )



def get_upgrade_level(user_id: int, upgrade_id: str):
    data = UPGRADES.get(upgrade_id)

    if not data:
        return 0

    field = data["field"]

    return get_user_field(
        user_id,
        field,
        0
    )

def get_luck_level(user_id: int, activity_name: str):

    field_map = {
        "fish": "fish_luck_level",
        "mine": "mine_luck_level",
    }

    field = field_map[activity_name]

    return get_user_field(
        user_id,
        field,
        0
    )

def get_tool_level(user_id: int, activity_name: str):

    field_map = {
        "fish": "fish_tool_level",
        "mine": "mine_tool_level",
    }

    field = field_map[activity_name]

    return get_user_field(
        user_id,
        field,
        1
    )

def get_user_field(user_id: int, field: str, default=0):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        f"""
        SELECT {field}
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    if not row:
        return default

    return row[0]

INVENTORY_PAGE_SIZE = 8
def get_inventory_pages(user_id: int):
    items = get_inventory(user_id)

    return [
        items[i:i + INVENTORY_PAGE_SIZE]
        for i in range(0, len(items), INVENTORY_PAGE_SIZE)
    ]

async def show_inventory(query, owner_id, page: int = 0):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)
    pages = get_inventory_pages(user_id)

    if not pages:
        text = (
            f"<b>{user_name}</b>\n"
            f"<code>- баланс: {balance}</code>\n\n"
            "🎒 <b>Инвентарь пуст.</b>"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(owner_id)
        )
        return

    page = max(0, min(page, len(pages) - 1))
    current = pages[page]

    text = (
        f"<b>{user_name}</b>\n"
        f"<code>- баланс: {balance}</code>\n\n"
        f"🎒 <b><u>Инвентарь</u></b>\n\n"
    )

    for item_id, amount in current:
        item = SHOP.get(item_id)
        name = item["name"] if item else item_id
        text += f"{name} <i>×{amount}</i>\n"

    keyboard = []

    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"eco_inventory_page_{page - 1}:{owner_id}"
            )
        )

    nav.append(
        InlineKeyboardButton(
            f"{page + 1}/{len(pages)}",
            callback_data=f"noop:{owner_id}"
        )
    )

    if page < len(pages) - 1:
        nav.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"eco_inventory_page_{page + 1}:{owner_id}"
            )
        )

    keyboard.append(nav)
    keyboard.append([    
        InlineKeyboardButton(
            "💢 Продать все",
            callback_data=f"eco_sell_inventory_all:{owner_id}"
            )
        ]
    )
    keyboard.append([
        InlineKeyboardButton(
            "Прод. повторки",
            callback_data=f"eco_sell_inventory_duplicates:{owner_id}"
        )]
    )
    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"eco_main_menu:{owner_id}"
        )
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

STORAGE_PAGE_SIZE = 8
def get_storage_pages(user_id: int):
    items = get_storage(user_id)

    return [
        items[i:i + STORAGE_PAGE_SIZE]
        for i in range(0, len(items), STORAGE_PAGE_SIZE)
    ]

async def show_storage(query, owner_id, page: int = 0):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)
    pages = get_storage_pages(user_id)

    if not pages:
        text = (
            f"<b>{user_name}</b>\n"
            f"<code>- баланс: {balance}</code>\n\n"
            "🕳 <b>Хранилище пустое.</b>"
        )

        await query.edit_message_text(
            text,
            parse_mode="HTML",
            reply_markup=get_goback_keyboard(owner_id)
        )
        return

    page = max(0, min(page, len(pages) - 1))
    current = pages[page]

    text = (
        f"<b>{user_name}</b>\n"
        f"<code>- баланс: {balance}</code>\n\n"
        "🕳 <b><u>Хранилище</u></b>\n\n"
    )

    for item_id, amount in current:
        item = STORAGE_ITEMS_INDEX.get(item_id)
        name = item["name"] if item else item_id
        text += f"{name} <i>×{amount}</i>\n"

    keyboard = []

    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"eco_storage_page_{page - 1}:{owner_id}"
            )
        )

    nav.append(
        InlineKeyboardButton(
            f"{page + 1}/{len(pages)}",
            callback_data=f"noop:{owner_id}"
        )
    )

    if page < len(pages) - 1:
        nav.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"eco_storage_page_{page + 1}:{owner_id}"
            )
        )

    keyboard.append(nav)
    
    keyboard.append([    
        InlineKeyboardButton(
            "💢 Продать все",
            callback_data=f"eco_sell_storage_all:{owner_id}"
            )
        ]
    )
    keyboard.append([
        InlineKeyboardButton(
            "Прод. повторки",
            callback_data=f"eco_sell_storage_duplicates:{owner_id}"
        )]
    )
    
    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"eco_main_menu:{owner_id}"
        )
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

SHOP_PAGE_SIZE = 6
def get_shop_pages():
    items = list(SHOP.items())

    pages = [
        items[i:i + SHOP_PAGE_SIZE]
        for i in range(0, len(items), SHOP_PAGE_SIZE)
    ]

    return pages

async def show_shop(query, owner_id, page: int = 0):

    pages = get_shop_pages()

    if not pages:
        await query.edit_message_text("🛒 Магазин пуст")
        return

    page = max(0, min(page, len(pages) - 1))
    current_page = pages[page]

    keyboard = []

    for item_id, item in current_page:
        keyboard.append([
            InlineKeyboardButton(
                item["name"],
                callback_data=f"eco_shop_item_{item_id}:{owner_id}"
            )
        ])

    nav_row = []

    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"eco_shop_page_{page - 1}:{owner_id}"
            )
        )

    nav_row.append(
        InlineKeyboardButton(
            f"{page + 1}/{len(pages)}",
            callback_data=f"noop:{owner_id}"
        )
    )

    if page < len(pages) - 1:
        nav_row.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"eco_shop_page_{page + 1}:{owner_id}"
            )
        )

    keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"eco_main_menu:{owner_id}"
        )
    ])

    await query.edit_message_text(
        "🛒 Магазин",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

UPGRADES_PAGE_SIZE = 2
def get_upgrades_pages():
    items = list(UPGRADES.items())

    return [
        items[i:i + UPGRADES_PAGE_SIZE]
        for i in range(0, len(items), UPGRADES_PAGE_SIZE)
    ]

async def show_upgrades(query, owner_id, page: int = 0):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    pages = get_upgrades_pages()

    if not pages:
        await query.edit_message_text("🧬 Апгрейды отсутствуют")
        return

    page = max(0, min(page, len(pages) - 1))
    current = pages[page]

    keyboard = []

    for upgrade_id, upgrade in current:
        keyboard.append([
            InlineKeyboardButton(
                upgrade["name"],
                callback_data=f"eco_upgrade_{upgrade_id}:{owner_id}"
            )
        ])

    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"eco_upgrades_page_{page - 1}:{owner_id}"
            )
        )

    nav.append(
        InlineKeyboardButton(
            f"{page + 1}/{len(pages)}",
            callback_data=f"noop:{owner_id}"
        )
    )

    if page < len(pages) - 1:
        nav.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"eco_upgrades_page_{page + 1}:{owner_id}"
            )
        )

    keyboard.append(nav)

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data=f"eco_main_menu:{owner_id}"
        )
    ])

    await query.edit_message_text(
        "🧬 Апгрейды",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_shop_item(query, item_id, status_text, owner_id):    

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)

    item = SHOP.get(item_id)
    if not item:
        return

    effects = [
        f"<code>• {k}: {v}</code>"
        for k, v in item["effect"].items()
    ]

    text = (
        f"{user_name}\n"
        f"<code>- баланс: {balance}</code>\n\n"
        f"<b><u>{item['name']}</u></b>\n\n"
        f"<i>{item['effect_name']}</i>\n\n"
        f"💰 <code>цена:</code> <b>{item['price']}</b>\n"
        f"📦 <code>тип:</code> {item['type']}\n"
        f"<code>🔍 загадочный текст:</code>\n"
        + "\n".join(effects)
    )

    if status_text:
        text = f"{text}\n\n{status_text}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🛒 Купить",
                callback_data=f"eco_buy_{item_id}:{owner_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=f"eco_shop:{owner_id}"
            )
        ]
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def show_upgrade_item(query, upgrade_id, status_text, owner_id):
    upgrade = UPGRADES.get(upgrade_id)

    if not upgrade:
        return

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)

    level = get_user_field(
        user_id,
        upgrade["field"],
        0
    )

    if "tool" in upgrade_id:
        level = max(level, 1)

    next_level = level + 1
    price = get_upgrade_price(upgrade_id, next_level)

    text = (
        f"{user_name}\n"
        f"<code>- баланс: {balance}</code>\n\n"
        f"<b><u>{upgrade['name']}</u></b>\n\n"
        f"<i>{upgrade['effect_name']}</i>\n"
        f"<i>Улучшение с {level} до уровня {next_level}</i>\n\n"
        f"💰 <code>цена:</code> <b>{price}</b>\n"
        f"📦 <code>тип:</code> улучшение"
    )

    if status_text:
        text = f"{text}\n\n{status_text}"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🧬 Купить",
                callback_data=f"eco_upgrade_buy_{upgrade_id}:{owner_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=f"eco_upgrades:{owner_id}"
            )
        ]
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )

def get_top_players(limit=10):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            telegram_name,
            fish_level,
            mine_level,
            (fish_level + mine_level) as total_level
        FROM users
        ORDER BY total_level DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()

    conn.close()

    return rows[:20]

async def show_top_players(query, owner_id):

    top = get_top_players()

    header = "🏆 Топ игроков\n\n"

    body = ""

    for place, row in enumerate(top, start=1):
        user_id, fish_level, mine_level, total = row

        body += (
            f"{place}. {user_id}\n"
            f"   🎣 {fish_level} | ⛏️ {mine_level}\n"
            f"   всего уровней: {total}\n\n"
        )

    full_text = header + body

    entities = [
        MessageEntity(
            type="expandable_blockquote",
            offset=len(header),
            length=tg_len(body)
        )
    ]

    await query.edit_message_text(
        full_text,
        entities=entities,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Назад",
                    callback_data=f"eco_main_menu:{owner_id}"
                )
            ]
        ])
    )

def tg_len(text: str) -> int:
            return len(text.encode("utf-16-le")) // 2

init_db()
build_item_index()


from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup

def get_main_keyboard(owner_id):

    return InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "〰️ Играть 〰️",
            callback_data=f"eco_actions:{owner_id}"
        )
    ],
    [
        InlineKeyboardButton(
            "🎒 Инвентарь",
            callback_data=f"eco_inventory:{owner_id}"
        ),
        InlineKeyboardButton(
            "🕳 Хранилище",
            callback_data=f"eco_storage:{owner_id}"
        )
    ],
    [
        InlineKeyboardButton(
            "🛒 Магазин",
            callback_data=f"eco_shop:{owner_id}"
        ),    
        InlineKeyboardButton(
            "🧬 Апгрейды",
            callback_data=f"eco_upgrades:{owner_id}"
        ),
    ],
    [
        InlineKeyboardButton(
            "🏆 Топ",
            callback_data=f"eco_top:{owner_id}"
        )
    ],
])

def get_actions_keyboard(owner_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎣 Рыбалка", callback_data=f"eco_fish:{owner_id}")
        ],
        [
            InlineKeyboardButton("⛏️ Шахта", callback_data=f"eco_mine:{owner_id}")
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"eco_main_menu:{owner_id}")
        ],
    ])

def get_goback_keyboard(owner_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️ Назад", callback_data=f"eco_main_menu:{owner_id}")
        ],
    ])

async def main_menu(update, context):

    user_id = update.message.from_user.id
    user_name = update.message.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)

    progress_lines = []

    for activity_name, activity in ACTIVITIES.items():

        level, xp, needed_xp = get_progress(user_id, activity_name)

        progress_lines.append(
            f"<code>- {activity['name']} lvl.{level} "
            f"({xp}/{needed_xp})</code>"
        )

    progress_text = "\n".join(progress_lines)

    text = (
        f"<b>{user_name}</b>\n"
        f"<code>- баланс: {balance}</code>\n"        
        f"{progress_text}"        
    )
    
    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(user_id)
    )

async def main_menu_query(query, actions: bool = False):

    user_id = query.from_user.id
    user_name = query.from_user.name

    ensure_user(user_id, user_name)

    balance = get_balance(user_id)

    progress_lines = []

    for activity_name, activity in ACTIVITIES.items():

        level, xp, needed_xp = get_progress(user_id, activity_name)

        progress_lines.append(
            f"<code>- {activity['name']} lvl.{level} "
            f"({xp}/{needed_xp})</code>"
        )

    progress_text = "\n".join(progress_lines)

    text = (
        f"<b>{user_name}</b>\n"
        f"<code>- баланс: {balance}</code>\n"
        f"{progress_text}"        
    )

    if actions:
        reply_markup=get_actions_keyboard(user_id)
    else:
        reply_markup=get_main_keyboard(user_id)

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

async def economy_callback(update, context):

    query = update.callback_query
    
    data = query.data
    user_id = query.from_user.id

    if ":" in data:
        payload, owner_id = data.rsplit(":", 1)
        try:
            owner_id = int(owner_id)
        except ValueError:
            return await query.answer("ошибка?", show_alert=True)

        if owner_id != user_id:
            return await query.answer("не твои кнопки, создай свои командой /economy", show_alert=True)
    else:
        return await query.answer("не твои кнопки, ошибка?", show_alert=True)

    await query.answer()

    data = payload

    if data == "eco_actions":
        await main_menu_query(query, True)

    elif data == "eco_main_menu":
        await main_menu_query(query, False)

    elif data == "eco_fish":
        await do_activity(query, "fish")

    elif data == "eco_mine":
        await do_activity(query, "mine")

    elif data == "eco_inventory":
        await show_inventory(query, owner_id)

    elif data == "eco_storage":
        await show_storage(query, owner_id)
    
    elif data == "eco_shop":
        await show_shop(query, owner_id)

    elif data.startswith("eco_shop_page_"):
        page = int(data.replace("eco_shop_page_", ""))
        await show_shop(query, owner_id, page)

    elif data.startswith("eco_inventory_page_"):
        page = int(data.replace("eco_inventory_page_", ""))
        await show_inventory(query, owner_id, page)

    elif data.startswith("eco_upgrades_page_"):
        page = int(data.replace("eco_upgrades_page_", ""))
        await show_upgrades(query, owner_id, page)

    elif data.startswith("eco_storage_page_"):
        page = int(data.replace("eco_storage_page_", ""))
        await show_storage(query, owner_id, page)

    elif data.startswith("eco_shop_item_"):
        item_id = data.replace(
            "eco_shop_item_",
            ""
        )

        await show_shop_item(
            query,
            item_id,
            None,
            owner_id
        )

    elif data.startswith("eco_buy_"):
        item_id = data.replace("eco_buy_", "")

        success, text = buy_item(
            query.from_user.id,
            item_id
        )

        await show_shop_item(
            query,
            item_id,
            text,
            owner_id
        )

    elif data == "eco_upgrades":
        await show_upgrades(query, owner_id)

    elif data.startswith("eco_upgrade_") and not data.startswith("eco_upgrade_buy_"):

        upgrade_id = data.replace(
            "eco_upgrade_",
            ""
        )

        await show_upgrade_item(
            query,
            upgrade_id,
            None,
            owner_id
        )

    elif data.startswith("eco_upgrade_buy_"):

        upgrade_id = data.replace(
            "eco_upgrade_buy_",
            ""
        )

        success, text = buy_upgrade(
            query.from_user.id,
            upgrade_id
        )

        await show_upgrade_item(
            query,
            upgrade_id,
            text,
            owner_id
        )

    elif data.startswith("eco_sell_inventory_duplicates"):
        await sell_inventory_duplicates(query)

    elif data.startswith("eco_sell_inventory_all"):
        await sell_inventory_all(query)

    elif data.startswith("eco_sell_storage_duplicates"):
        await sell_storage_duplicates(query)

    elif data.startswith("eco_sell_storage_all"):
        await sell_storage_all(query)

    elif data == "eco_top":
        await show_top_players(query, owner_id)