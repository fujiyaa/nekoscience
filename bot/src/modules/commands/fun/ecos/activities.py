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

{"id": "fish_tsundere_koi", "name": "🎀 Цундере кои", "min_level": 12, "weight": 2, "coins": (120, 220), "xp": 100, "rarity": "очень редкое"},
{"id": "fish_neko_salmon", "name": "🐱 Неко-лосось", "min_level": 14, "weight": 2, "coins": (140, 260), "xp": 120, "rarity": "очень редкое"},
{"id": "fish_magical_girl_tuna", "name": "✨ Тунец волшебницы", "min_level": 15, "weight": 2, "coins": (150, 280), "xp": 130, "rarity": "очень редкое"},
{"id": "fish_kitsune_eel", "name": "🦊 Лисий угорь", "min_level": 16, "weight": 2, "coins": (170, 300), "xp": 140, "rarity": "очень редкое"},
{"id": "fish_sakura_carp", "name": "🌸 Сакура-карп", "min_level": 18, "weight": 2, "coins": (180, 320), "xp": 150, "rarity": "очень редкое"},
{"id": "fish_maid_perch", "name": "☕ Горничная-окунь", "min_level": 20, "weight": 2, "coins": (200, 360), "xp": 170, "rarity": "очень редкое"},
{"id": "fish_yandere_pike", "name": "🔪 Яндере-щука", "min_level": 22, "weight": 1, "coins": (240, 420), "xp": 200, "rarity": "очень редкое"},
{"id": "fish_samurai_swordfish", "name": "⚔ Самурайская рыба-меч", "min_level": 24, "weight": 1, "coins": (260, 460), "xp": 220, "rarity": "очень редкое"},
{"id": "fish_ninja_barracuda", "name": "🥷 Ниндзя-барракуда", "min_level": 25, "weight": 1, "coins": (280, 500), "xp": 240, "rarity": "очень редкое"},
{"id": "fish_spirit_koi", "name": "👻 Духовный кои", "min_level": 27, "weight": 1, "coins": (300, 550), "xp": 260, "rarity": "очень редкое"},
{"id": "fish_moon_princess", "name": "🌙 Лунная принцесса", "min_level": 30, "weight": 1, "coins": (350, 650), "xp": 300, "rarity": "очень редкое"},
{"id": "fish_dragon_waifu", "name": "🐉 Драконья вайфу", "min_level": 32, "weight": 1, "coins": (400, 750), "xp": 340, "rarity": "очень редкое"},
{"id": "fish_mecha_tuna", "name": "🤖 Меха-тунец", "min_level": 35, "weight": 1, "coins": (500, 900), "xp": 400, "rarity": "очень редкое"},
{"id": "fish_holy_miko", "name": "⛩ Священная мико", "min_level": 38, "weight": 1, "coins": (650, 1200), "xp": 500, "rarity": "очень редкое"},
{"id": "fish_oni_catfish", "name": "👹 Они-сом", "min_level": 40, "weight": 1, "coins": (800, 1500), "xp": 600, "rarity": "очень редкое"},
{"id": "fish_cosmic_idol", "name": "🎤 Космический идол", "min_level": 42, "weight": 1, "coins": (1000, 1800), "xp": 700, "rarity": "очень редкое"},
{"id": "fish_void_chan", "name": "🖤 Пустота-тян", "min_level": 45, "weight": 1, "coins": (1300, 2400), "xp": 850, "rarity": "очень редкое"},
{"id": "fish_galaxy_koi", "name": "🌌 Галактический кои", "min_level": 47, "weight": 1, "coins": (1600, 2800), "xp": 1000, "rarity": "очень редкое"},
{"id": "fish_anime_protagonist", "name": "⭐ Рыба-протагонист", "min_level": 50, "weight": 1, "coins": (2500, 4500), "xp": 1500, "rarity": "очень редкое"},
{"id": "fish_goddess_of_ocean", "name": "👑 Богиня океана", "min_level": 50, "weight": 1, "coins": (3000, 5500), "xp": 1800, "rarity": "очень редкое"},

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


{"id": "fish_perch_epic", "name": "🌑 Теневой окунь", "min_level": 1, "weight": 12, "coins": (18, 30), "xp": 18, "rarity": "эпическое"},
{"id": "fish_carp_epic", "name": "🌑 Лунный карп", "min_level": 1, "weight": 10, "coins": (22, 35), "xp": 22, "rarity": "эпическое"},

{"id": "fish_eel_epic", "name": "🌑 Буревестник-угорь", "min_level": 2, "weight": 9, "coins": (28, 45), "xp": 28, "rarity": "эпическое"},
{"id": "fish_bass_epic", "name": "🌑 Глубинный басс", "min_level": 3, "weight": 8, "coins": (25, 40), "xp": 25, "rarity": "эпическое"},

{"id": "fish_bream_epic", "name": "🌑 Серый лещ туманов", "min_level": 3, "weight": 7, "coins": (30, 50), "xp": 30, "rarity": "эпическое"},
{"id": "fish_salmon_epic", "name": "🌑 Тёмный лосось", "min_level": 4, "weight": 7, "coins": (35, 60), "xp": 35, "rarity": "эпическое"},

{"id": "fish_pike_epic", "name": "🌑 Хищная тень-щука", "min_level": 5, "weight": 6, "coins": (45, 80), "xp": 45, "rarity": "эпическое"},
{"id": "fish_piranha_epic", "name": "🌑 Кровавая пирамида", "min_level": 5, "weight": 6, "coins": (40, 75), "xp": 40, "rarity": "эпическое"},

{"id": "fish_tuna_epic", "name": "🌑 Штормовой тунец", "min_level": 6, "weight": 5, "coins": (50, 90), "xp": 50, "rarity": "эпическое"},
{"id": "fish_halibut_epic", "name": "🌑 Ледяной палтус", "min_level": 6, "weight": 5, "coins": (55, 95), "xp": 55, "rarity": "эпическое"},

{"id": "fish_electric_eel_epic", "name": "🌑 Грозовой угорь", "min_level": 7, "weight": 4, "coins": (70, 120), "xp": 70, "rarity": "эпическое"},
{"id": "fish_blobfish_epic", "name": "🌑 Искажённая глубина", "min_level": 7, "weight": 4, "coins": (65, 115), "xp": 65, "rarity": "эпическое"},

{"id": "fish_swordfish_epic", "name": "🌑 Чёрный клинок", "min_level": 8, "weight": 3, "coins": (90, 150), "xp": 90, "rarity": "эпическое"},
{"id": "fish_goldfish_epic", "name": "🌑 Поглощённая золото", "min_level": 9, "weight": 3, "coins": (120, 220), "xp": 120, "rarity": "эпическое"},

{"id": "fish_catfish_giant_epic", "name": "🌑 Титан глубин", "min_level": 10, "weight": 3, "coins": (110, 200), "xp": 110, "rarity": "эпическое"},

{"id": "fish_arowana_epic", "name": "🌑 Хищная аравана", "min_level": 6, "weight": 4, "coins": (75, 130), "xp": 75, "rarity": "эпическое"},
{"id": "fish_zander_epic", "name": "🌑 Теневая судачья стая", "min_level": 5, "weight": 4, "coins": (70, 125), "xp": 70, "rarity": "эпическое"},

{"id": "fish_grayling_epic", "name": "🌑 Морозный хариус", "min_level": 6, "weight": 4, "coins": (80, 140), "xp": 80, "rarity": "эпическое"},

{"id": "fish_snakehead_epic", "name": "🌑 Ядовитый змееголов", "min_level": 7, "weight": 3, "coins": (100, 180), "xp": 100, "rarity": "эпическое"},

{"id": "fish_manta_ray_epic", "name": "🌑 Призрачная манта", "min_level": 9, "weight": 2, "coins": (150, 260), "xp": 150, "rarity": "эпическое"},

{"id": "fish_red_snapper_epic", "name": "🌑 Алый глубинный снэппер", "min_level": 12, "weight": 3, "coins": (180, 320), "xp": 180, "rarity": "эпическое"},

{"id": "fish_groupers_epic", "name": "🌑 Каменный группер", "min_level": 15, "weight": 2, "coins": (220, 400), "xp": 220, "rarity": "эпическое"},

{"id": "fish_mahi_mahi_epic", "name": "🌑 Плазменный махи-махи", "min_level": 10, "weight": 3, "coins": (140, 250), "xp": 140, "rarity": "эпическое"},

{"id": "fish_arapaima_epic", "name": "🌑 Полуночная арапайма", "min_level": 25, "weight": 2, "coins": (500, 900), "xp": 500, "rarity": "эпическое"},

{"id": "fish_sailfish_epic", "name": "🌑 Теневой парусник", "min_level": 30, "weight": 1, "coins": (800, 1400), "xp": 800, "rarity": "эпическое"},

{"id": "fish_megalodon_epic", "name": "🌑 Прототип мегалодона", "min_level": 35, "weight": 1, "coins": (1200, 2200), "xp": 1200, "rarity": "эпическое"},

{"id": "fish_void_fish_epic", "name": "🌑 Эхо пустоты", "min_level": 50, "weight": 1, "coins": (4000, 8000), "xp": 2500, "rarity": "эпическое"},


{"id": "fish_perch_veryrare", "name": "🌫 Туманный окунь", "min_level": 3, "weight": 18, "coins": (20, 35), "xp": 22, "rarity": "очень редкое"},
{"id": "fish_carp_veryrare", "name": "🌫 Глубинный карп", "min_level": 3, "weight": 16, "coins": (25, 45), "xp": 28, "rarity": "очень редкое"},

{"id": "fish_som_veryrare", "name": "🌫 Тихий сом бездны", "min_level": 4, "weight": 14, "coins": (35, 60), "xp": 35, "rarity": "очень редкое"},
{"id": "fish_lesh_veryrare", "name": "🌫 Затонувший лещ", "min_level": 4, "weight": 15, "coins": (30, 55), "xp": 32, "rarity": "очень редкое"},

{"id": "fish_pike_veryrare", "name": "🌫 Оскаленная щука тумана", "min_level": 5, "weight": 12, "coins": (50, 90), "xp": 50, "rarity": "очень редкое"},
{"id": "fish_ugor_veryrare", "name": "🌫 Электрический призрачный угорь", "min_level": 5, "weight": 10, "coins": (60, 110), "xp": 60, "rarity": "очень редкое"},

{"id": "fish_tuna_veryrare", "name": "🌫 Буревестный тунец", "min_level": 6, "weight": 10, "coins": (80, 140), "xp": 75, "rarity": "очень редкое"},
{"id": "fish_salmon_veryrare", "name": "🌫 Северный лосось теней", "min_level": 6, "weight": 11, "coins": (70, 130), "xp": 70, "rarity": "очень редкое"},

{"id": "fish_swordfish_veryrare", "name": "🌫 Ржавый клинок океана", "min_level": 8, "weight": 6, "coins": (120, 200), "xp": 120, "rarity": "очень редкое"},
{"id": "fish_electric_eel_veryrare", "name": "🌫 Разрядный угорь", "min_level": 7, "weight": 8, "coins": (110, 190), "xp": 110, "rarity": "очень редкое"},

{"id": "fish_goldfish_veryrare", "name": "🌫 Потускневшая золотая рыбка", "min_level": 9, "weight": 5, "coins": (180, 300), "xp": 160, "rarity": "очень редкое"},
{"id": "fish_blobfish_veryrare", "name": "🌫 Давление глубин", "min_level": 7, "weight": 7, "coins": (140, 240), "xp": 130, "rarity": "очень редкое"},

{"id": "fish_catfish_giant_veryrare", "name": "🌫 Старый гигант сомов", "min_level": 10, "weight": 4, "coins": (200, 350), "xp": 180, "rarity": "очень редкое"},

{"id": "fish_arowana_veryrare", "name": "🌫 Зеркальная аравана", "min_level": 6, "weight": 8, "coins": (100, 180), "xp": 95, "rarity": "очень редкое"},
{"id": "fish_zander_veryrare", "name": "🌫 Серый хищник глубин", "min_level": 5, "weight": 9, "coins": (90, 160), "xp": 85, "rarity": "очень редкое"},

{"id": "fish_manta_ray_veryrare", "name": "🌫 Тень манты", "min_level": 9, "weight": 3, "coins": (250, 420), "xp": 220, "rarity": "очень редкое"},

{"id": "fish_arapaima_veryrare", "name": "🌫 Огромная арапайма тумана", "min_level": 25, "weight": 2, "coins": (900, 1600), "xp": 800, "rarity": "очень редкое"},
{"id": "fish_megalodon_veryrare", "name": "🌫 Реликтовый мегалодон", "min_level": 35, "weight": 1, "coins": (2000, 3500), "xp": 1500, "rarity": "очень редкое"},
{"id": "fish_void_fish_veryrare", "name": "🌫 Стабильная пустота", "min_level": 50, "weight": 1, "coins": (6000, 10000), "xp": 3000, "rarity": "очень редкое"},


{"id": "trash_boot_old", "name": "👢 Старая сапога", "min_level": 1, "weight": 2, "coins": (0, 2), "xp": 1, "rarity": "обычное"},
{"id": "trash_can_lid", "name": "🪣 Крышка от ведра", "min_level": 1, "weight": 2, "coins": (0, 2), "xp": 1, "rarity": "обычное"},
{"id": "trash_plastic_bag", "name": "🛍 Пакет из глубин", "min_level": 1, "weight": 1, "coins": (0, 1), "xp": 1, "rarity": "обычное"},
{"id": "trash_algae", "name": "🌿 Комок водорослей", "min_level": 1, "weight": 3, "coins": (0, 1), "xp": 1, "rarity": "обычное"},
{"id": "trash_bottle_cap", "name": "🔵 Пластиковая крышка", "min_level": 1, "weight": 2, "coins": (0, 1), "xp": 1, "rarity": "обычное"},

{"id": "trash_wood_plank", "name": "🪵 Гнилая доска", "min_level": 1, "weight": 2, "coins": (0, 3), "xp": 2, "rarity": "обычное"},
{"id": "trash_rope_knot", "name": "🪢 Узел старой верёвки", "min_level": 2, "weight": 2, "coins": (0, 2), "xp": 1, "rarity": "обычное"},
{"id": "trash_can_rusty", "name": "🪨 Ржавая банка", "min_level": 2, "weight": 2, "coins": (0, 3), "xp": 2, "rarity": "обычное"},

{"id": "trash_sock", "name": "🧦 Одинокий носок", "min_level": 2, "weight": 1, "coins": (0, 1), "xp": 1, "rarity": "обычное"},
{"id": "trash_tire_piece", "name": "🛞 Кусок шины", "min_level": 3, "weight": 2, "coins": (1, 3), "xp": 2, "rarity": "обычное"},

{"id": "trash_fishing_line", "name": "🎣 Спутанная леска", "min_level": 3, "weight": 2, "coins": (0, 2), "xp": 2, "rarity": "обычное"},
{"id": "trash_hook_old", "name": "🪝 Ржавый крючок", "min_level": 3, "weight": 1, "coins": (1, 4), "xp": 3, "rarity": "обычное"},

{"id": "trash_tin_can", "name": "🥫 Пустая банка", "min_level": 3, "weight": 2, "coins": (0, 3), "xp": 2, "rarity": "обычное"},
{"id": "trash_glass_shard", "name": "🪞 Осколок стекла", "min_level": 4, "weight": 1, "coins": (1, 5), "xp": 3, "rarity": "обычное"},

{"id": "trash_broken_watch", "name": "⌚ Поломанные часы", "min_level": 4, "weight": 1, "coins": (2, 6), "xp": 4, "rarity": "обычное"},
{"id": "trash_metal_scrap", "name": "⚙️ Металлолом", "min_level": 4, "weight": 2, "coins": (1, 4), "xp": 3, "rarity": "обычное"},

{"id": "trash_shoe_single", "name": "👟 Один кроссовок", "min_level": 4, "weight": 1, "coins": (1, 5), "xp": 3, "rarity": "обычное"},
{"id": "trash_lighter_wet", "name": "🔥 Мокрая зажигалка", "min_level": 5, "weight": 1, "coins": (2, 6), "xp": 4, "rarity": "обычное"},

{"id": "trash_phone_old", "name": "📱 Утопленный телефон", "min_level": 5, "weight": 1, "coins": (5, 10), "xp": 6, "rarity": "обычное"},
{"id": "trash_camera_underwater", "name": "📷 Камера без души", "min_level": 5, "weight": 1, "coins": (3, 8), "xp": 5, "rarity": "обычное"},

{"id": "trash_anchor_small", "name": "⚓ Сломанный якорь", "min_level": 5, "weight": 1, "coins": (4, 10), "xp": 6, "rarity": "обычное"},

{"id": "trash_fake_pearl", "name": "🦪 Поддельная жемчужина", "min_level": 4, "weight": 1, "coins": (10, 20), "xp": 8, "rarity": "обычное"},


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