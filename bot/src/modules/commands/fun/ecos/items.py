xp_potion_text = "Бустит получение XP\nМожет сломаться"
coin_potion_text = "Бустит получение денег\nМожет сломаться"
all_potion_text = "Слабый буст\n(денег и опыта)\nМожет сломаться"
trade_potion_text = "Рандомно бустит денеги\nШанс проиграть деньги\nМожет сломаться"
SHOP = {    
    "xp_potion_f": {
        "name": "🧪 Зелье опыта (плохое)",
        "effect_name": xp_potion_text,
        "price": 25,
        "type": "зелье",
        "effect": {
            "xp_buff": 1.5,
            "vanish_chance": 0.40
        },
    },
    "coin_potion_f": {
        "name": "🌡 Зелье денег (плохое)",
        "effect_name": coin_potion_text,
        "price": 50,
        "type": "зелье",
        "effect": {
            "coin_buff": 1.5,
            "vanish_chance": 0.40
        },
    },
    "all_potion_f": {
        "name": "🧴 Зелье всего (плохое)",
        "effect_name": all_potion_text,
        "price": 25,
        "type": "зелье",
        "effect": {
            "coin_buff": 1.25,
            "xp_buff": 1.25,
            "vanish_chance": 0.25
        },
    },
    "xp_potion_e": {
        "name": "🧪 Зелье опыта E",
        "effect_name": xp_potion_text,
        "price": 200,
        "type": "зелье",
        "effect": {
            "xp_buff": 2.0,
            "vanish_chance": 0.20
        },
    },
    "coin_potion_e": {
        "name": "🌡 Зелье денег E",
        "effect_name": coin_potion_text,
        "price": 500,
        "type": "зелье",
        "effect": {
            "coin_buff": 2.0,
            "vanish_chance": 0.25
        },
    },
    "all_potion_e": {
        "name": "🧴 Зелье всего E",
        "effect_name": all_potion_text,
        "price": 550,
        "type": "зелье",
        "effect": {
            "coin_buff": 2.0,
            "xp_buff": 1.8,
            "vanish_chance": 0.05
        },
    },
    "xp_potion_d": {
        "name": "🧪 Зелье опыта D",
        "effect_name": xp_potion_text,
        "price": 600,
        "type": "зелье",
        "effect": {
            "xp_buff": 3.5,
            "vanish_chance": 0.025
        },
    },
    "coin_potion_d": {
        "name": "🌡 Зелье денег D",
        "effect_name": coin_potion_text,
        "price": 500,
        "type": "зелье",
        "effect": {
            "coin_buff": 5.0,
            "vanish_chance": 0.5
        },
    },
    "all_potion_d": {
        "name": "🧴 Зелье всего D",
        "effect_name": all_potion_text,
        "price": 950,
        "type": "зелье",
        "effect": {
            "coin_buff": 3.0,
            "xp_buff": 2.5,
            "vanish_chance": 0.08
        },
    },
    "xp_potion_c": {
        "name": "🧪 Зелье опыта C",
        "effect_name": xp_potion_text,
        "price": 1000,
        "type": "зелье",
        "effect": {
            "xp_buff": 4.5,
            "vanish_chance": 0.025
        },
    },
    "coin_potion_c": {
        "name": "🌡 Зелье денег C",
        "effect_name": coin_potion_text,
        "price": 2000,
        "type": "зелье",
        "effect": {
            "coin_buff": 4.5,
            "vanish_chance": 0.025
        },
    },
    "all_potion_c": {
        "name": "🧴 Зелье всего C",
        "effect_name": all_potion_text,
        "price": 4600,
        "type": "зелье",
        "effect": {
            "coin_buff": 4.8,
            "xp_buff": 4.2,
            "vanish_chance": 0.01
        },
    },
    "xp_potion_b": {
        "name": "🧪 Зелье опыта B",
        "effect_name": xp_potion_text,
        "price": 5000,
        "type": "зелье",
        "effect": {
            "xp_buff": 6.7,
            "vanish_chance": 0.17
        },
    },
    "coin_potion_b": {
        "name": "🌡 Зелье денег B",
        "effect_name": coin_potion_text,
        "price": 18000,
        "type": "зелье",
        "effect": {
            "coin_buff": 5.0,
            "vanish_chance": 0.05
        },
    },
    "all_potion_b": {
        "name": "🧴 Зелье всего B",
        "effect_name": all_potion_text,
        "price": 25,
        "type": "зелье",
        "effect": {
            "coin_buff": 5.00,
            "xp_buff": 5.00,
            "vanish_chance": 0.01
        },
    },
    "xp_potion_a": {
        "name": "🧪 Зелье опыта A",
        "effect_name": xp_potion_text,
        "price": 50000,
        "type": "зелье",
        "effect": {
            "xp_buff": 6.0,
            "vanish_chance": 0.009
        },
    },
    "coin_potion_a": {
        "name": "🌡 Зелье денег A",
        "effect_name": coin_potion_text,
        "price": 115000,
        "type": "зелье",
        "effect": {
            "coin_buff": 7.0,
            "vanish_chance": 0.009
        },
    },
    "all_potion_f": {
        "name": "🧴 Зелье всего A",
        "effect_name": all_potion_text,
        "price": 35000,
        "type": "зелье",
        "effect": {
            "coin_buff": 6.25,
            "xp_buff": 7.25,
            "vanish_chance": 0.004
        },
    },
    "xp_potion_s": {
        "name": "🧪 Зелье опыта S",
        "effect_name": xp_potion_text,
        "price": 100000,
        "type": "зелье",
        "effect": {
            "xp_buff": 8.5,
            "vanish_chance": 0.005
        },
    },
    "coin_potion_s": {
        "name": "🌡 Зелье денег S",
        "effect_name": coin_potion_text,
        "price": 600000,
        "type": "зелье",
        "effect": {
            "coin_buff": 9.5,
            "vanish_chance": 0.001
        },
    },
    "all_potion_f": {
        "name": "🧴 Зелье всего S",
        "effect_name": all_potion_text,
        "price": 250000,
        "type": "зелье",
        "effect": {
            "coin_buff": 8.00,
            "xp_buff": 7.5,
            "vanish_chance": 0.005
        },
    },
    "random_potion_x": {
        "name": "🧪 Радиоктивное зелье",
        "effect_name": "Эффекты неизвестны\nМожет сломаться",
        "price": 1000000,
        "type": "зелье",
        "effect": {
            "random_buff": 25.0,
            "vanish_chance": 0.001
        },
    }, 
    "collectable_1": {
        "name": "👤 Стас",
        "effect_name": "Талисман\nНе имет эффектов\nМожет сломаться",
        "price": 1,
        "type": "талисман",
        "effect": {
            "aura_buff": 1.25,
            "vanish_chance": 0.00001
        },
    },
    "collectable_2": {
        "name": "🧲 Магнит денег (слабый)",
        "effect_name": "Талисман\nСлабый бафф денег\nМожет сломаться",
        "price": 25000,
        "type": "талисман",
        "effect": {
            "coin_buff": 2.0,
            "vanish_chance": 0.0001
        },
    },
    "trade_b": {
        "name": "🍢 Сделка B",
        "effect_name": trade_potion_text,
        "price": 1,
        "type": "казино",
        "effect": {
            "negative_coin_chance": 0.50,
            "vanish_chance": 0.0001
        },
    },
    "trade_a": {
        "name": "🍢 Сделка A",
        "effect_name": trade_potion_text,
        "price": 100,
        "type": "казино",
        "effect": {
            "coin_buff": 10.0,
            "negative_coin_chance": 0.60,
            "vanish_chance": 0.025
        },
    },
    "trade_x": {
        "name": "🍢 Сделка S",
        "effect_name": trade_potion_text,
        "price": 10000,
        "type": "казино",
        "effect": {
            "coin_buff": 15.0,
            "negative_coin_chance": 0.40,
            "vanish_chance": 0.005
        },
    },
    "trade_ss": {
        "name": "🍢 Сделка S+",
        "effect_name": trade_potion_text,
        "price": 10000000,
        "type": "казино",
        "effect": {
            "coin_buff": 30.0,
            "negative_coin_chance": 0.30,
            "vanish_chance": 0.001
        },
    },
    "gamble_coin_1": {
        "name": "🌶 Гемблинг перец I",
        "effect_name": "Рандомный множитель денег\nМожно проиграть все\nМожет сломаться",
        "price": 50,
        "type": "казино",
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
        "type": "казино",
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
        "type": "казино",
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
        "type": "казино",
        "effect": {
            "xp_multiplier_random": 5.0,
            "negative_coin_chance": 0.50,
            "vanish_chance": 0.05
        },
    },
    "xp_trade_f": {
        "name": "🩸 Трейд ХР (подделка)",
        "effect_name": "Множитель XP\nТратит деньги\nМожет сломаться",
        "price": 100,
        "type": "казино",
        "effect": {
            "xp_multiplier_random": 3.0,
            "coin_multiplier_random": 4.0,
            "negative_coin_chance": 0.70,
            "vanish_chance": 0.02
        },
    },
    "xp_trade": {
        "name": "🩸 Трейд ХР",
        "effect_name": "Множитель XP\nТратит деньги\nМожет сломаться",
        "price": 1000,
        "type": "казино",
        "effect": {
            "xp_multiplier_random": 5.0,
            "coin_multiplier_random": 5.0,
            "negative_coin_chance": 0.99,
            "vanish_chance": 0.01
        },
    },
    "xp_trade_2": {
        "name": "🩸 Трейд ХР 2",
        "effect_name": "Множитель XP\nТратит деньги\nМожет сломаться",
        "price": 5000,
        "type": "казино",
        "effect": {
            "xp_multiplier_random": 10.0,
            "coin_multiplier_random": 8.0,
            "negative_coin_chance": 0.99,
            "vanish_chance": 0.001
        },
    },
    "xp_trade_3": {
        "name": "🩸 Трейд ХР 3",
        "effect_name": "Множитель XP\nТратит деньги\nМожет сломаться",
        "price": 100000,
        "type": "казино",
        "effect": {
            "xp_multiplier_random": 30.0,
            "coin_multiplier_random": 25.0,
            "negative_coin_chance": 0.99,
            "vanish_chance": 0.0005
        },
    },
    "item_trade_fish_f": {
        "name": "💎 Продажа рыбы (новичок)",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 100,
        "type": "торговля",
        "effect": {
            "trade_type": "fish",
            "trade_multiplier": 3,
            "vanish_chance": 0.10
        },
    },
    "item_trade_mine_f": {
        "name": "💎 Продажа шахты (новичок)",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 100,
        "type": "торговля",
        "effect": {
            "trade_type": "mine",
            "trade_multiplier": 3,
            "vanish_chance": 0.10
        },
    },
    "item_trade_fish": {
        "name": "💎 Продажа рыбы I",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 1000,
        "type": "торговля",
        "effect": {
            "trade_type": "fish",
            "trade_multiplier": 10,
            "vanish_chance": 0.05
        },
    },
    "item_trade_mine": {
        "name": "💎 Продажа шахты I",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 1000,
        "type": "торговля",
        "effect": {
            "trade_type": "mine",
            "trade_multiplier": 10,
            "vanish_chance": 0.05
        },
    },
    "item_trade_fish_2": {
        "name": "💎 Продажа рыбы II",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 2600,
        "type": "торговля",
        "effect": {
            "trade_type": "fish",
            "trade_multiplier": 20,
            "vanish_chance": 0.05
        },
    },
    "item_trade_mine_2": {
        "name": "💎 Продажа шахты II",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 2600,
        "type": "торговля",
        "effect": {
            "trade_type": "mine",
            "trade_multiplier": 20,
            "vanish_chance": 0.05
        },
    },
    "item_trade_fish_3": {
        "name": "💎 Продажа рыбы III",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 18000,
        "type": "торговля",
        "effect": {
            "trade_type": "fish",
            "trade_multiplier": 30,
            "vanish_chance": 0.025
        },
    },
    "item_trade_mine_3": {
        "name": "💎 Продажа шахты III",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 18000,
        "type": "торговля",
        "effect": {
            "trade_type": "mine",
            "trade_multiplier": 30,
            "vanish_chance": 0.025
        },
    },
    "item_trade_fish_4": {
        "name": "💎 Продажа рыбы IV",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 120000,
        "type": "торговля",
        "effect": {
            "trade_type": "fish",
            "trade_multiplier": 50,
            "vanish_chance": 0.001
        },
    },
    "item_trade_mine_4": {
        "name": "💎 Продажа шахты IV",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться",
        "price": 120000,
        "type": "торговля",
        "effect": {
            "trade_type": "mine",
            "trade_multiplier": 50,
            "vanish_chance": 0.001
        },
    },
    "item_reset_capsule": {
        "name": "🧬 Капсула СБРОСА",
        "effect_name": "Полностью сбрасывает статы\nдля любителей казино\n(и уровни)",
        "price": 0,
        "type": "капсула",
        "effect": {
            "reset_stats": True
        }
    },
}



# SHOP_CATEGORIES = get_shop_categories()