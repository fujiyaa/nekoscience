xp_potion_text = "Бустит получение XP\nМожет сломаться"
coin_potion_text = "Бустит получение денег\nМожет сломаться"
all_potion_text = "Слабый буст\n(денег и опыта)\nМожет сломаться"
trade_potion_text = "Рандомно бустит денеги\nШанс проиграть деньги\nМожет сломаться"
sell_buff_text = "Бафф стоимости продажи\n(из хранилища)\nМожет сломаться"

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
        "price": 12700,
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
    "all_potion_a": {
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
    "all_potion_s": {
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
    "xp_potion_ss": {
        "name": "🧪 Зелье опыта SS",
        "effect_name": xp_potion_text,
        "price": 340000,
        "type": "зелье",
        "effect": {
            "xp_buff": 19.5,
            "vanish_chance": 0.025
        },
    },
    "coin_potion_ss": {
        "name": "🌡 Зелье денег SS",
        "effect_name": coin_potion_text,
        "price": 890000,
        "type": "зелье",
        "effect": {
            "coin_buff": 18.5,
            "vanish_chance": 0.025
        },
    },
    "all_potion_ss": {
        "name": "🧴 Зелье всего SS",
        "effect_name": all_potion_text,
        "price": 1500000,
        "type": "зелье",
        "effect": {
            "coin_buff": 13.0,
            "xp_buff": 10.0,
            "vanish_chance": 0.005
        },
    },
    "random_potion_x": {
        "name": "🧪 Радиоактивное зелье",
        "effect_name": "Эффекты неизвестны\nМожет сломаться",
        "price": 10000000,
        "type": "зелье, казино",
        "effect": {
            "random_buff": 250.0,
            "vanish_chance": 0.99
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
        "effect_name": "Талисман\nСлабый бафф денег\nМожет сломаться\n(но маловероятно)",
        "price": 35000,
        "type": "талисман",
        "effect": {
            "coin_buff": 2.5,
            "vanish_chance": 0.00001
        },
    },
    "collectable_3": {
        "name": "🧲 Магнит опыта (слабый)",
        "effect_name": "Талисман\nСлабый бафф опыта\nМожет сломаться\n(но маловероятно)",
        "price": 5000,
        "type": "талисман",
        "effect": {
            "xp_buff": 1.2,
            "vanish_chance": 0.00005
        },
    },
    "collectable_4": {
        "name": "⚛️ Стабильный тотем",
        "effect_name": "Талисман\nСлабый рандом денег\nМожет сломаться\n(но маловероятно)",
        "price": 7500,
        "type": "талисман, казино",
        "effect": {
            "coin_multiplier_random": 1.5,
            "vanish_chance": 0.000001
        },
    },
    "collectable_5": {
        "name": "🧲 Магнит денег (средний)",
        "effect_name": "Талисман\nСредний бафф денег\nМожет сломаться\n(но маловероятно)",
        "price": 6800000,
        "type": "талисман",
        "effect": {
            "coin_buff": 6.90,
            "vanish_chance": 0.000025
        },
    },
    "collectable_6": {
        "name": "🧲 Магнит опыта (средний)",
        "effect_name": "Талисман\nСредний бафф опыта\nМожет сломаться\n(но маловероятно)",
        "price": 4500000,
        "type": "талисман",
        "effect": {
            "xp_buff": 4.25,
            "vanish_chance": 0.000025
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
    "trade_sss": {
        "name": "🍢 Сделка SS",
        "effect_name": trade_potion_text,
        "price": 1000000000,
        "type": "казино",
        "effect": {
            "coin_buff": 100.0,
            "negative_coin_chance": 0.30,
            "vanish_chance": 0.0005
        },
    },
    "gamble_coin_1": {
        "name": "🌶 Гемблинг перец I",
        "effect_name": "Рандомный множитель денег\nМожно проиграть все\nМожет сломаться",
        "price": 150,
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
            "coin_multiplier_random": 20.0,
            "negative_coin_chance": 0.50,
            "vanish_chance": 0.05
        },
    },
    "gamble_coin_3": {
        "name": "🌶 Гемблинг перец III",
        "effect_name": "Рандомный множитель денег\nМожно проиграть все\nМожет сломаться",
        "price": 10000,
        "type": "казино",
        "effect": {
            "coin_multiplier_random": 30.0,
            "negative_coin_chance": 0.60,
            "vanish_chance": 0.025
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
    "gamble_xp_3": {
        "name": "🥖 Гемблинг батон III",
        "effect_name": "Рандомный множитель XP\nМожет сломаться",
        "price": 25000,
        "type": "казино",
        "effect": {
            "xp_multiplier_random": 7.5,
            "negative_coin_chance": 0.80,
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
    "item_trade_forest_f": {
        "name": "💎 Продажа леса",
        "effect_name": sell_buff_text,
        "price": 450,
        "type": "торговля",
        "effect": {
            "trade_type": "forest",
            "trade_multiplier": 15.0,
            "vanish_chance": 0.0001
        },
    },
    "item_trade_battle_f": {
        "name": "💎 Продажа сражения",
        "effect_name": sell_buff_text,
        "price": 750000,
        "type": "торговля",
        "effect": {
            "trade_type": "battle",
            "trade_multiplier": 3,
            "vanish_chance": 0.0001
        },
    },
    "item_trade_fish_f": {
        "name": "💎 Продажа рыбы (новичок)",
        "effect_name": sell_buff_text,
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
        "effect_name": sell_buff_text,
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
        "effect_name": sell_buff_text,
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
        "effect_name": sell_buff_text,
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
        "effect_name": sell_buff_text,
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
        "effect_name": sell_buff_text,
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
        "effect_name": sell_buff_text,
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
        "effect_name": sell_buff_text,
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
        "effect_name": sell_buff_text,
        "price": 120000,
        "type": "торговля",
        "effect": {
            "trade_type": "fish",
            "trade_multiplier": 50,
            "vanish_chance": 0.004
        },
    },
    "item_trade_mine_4": {
        "name": "💎 Продажа шахты IV",
        "effect_name": sell_buff_text,
        "price": 120000,
        "type": "торговля",
        "effect": {
            "trade_type": "mine",
            "trade_multiplier": 50,
            "vanish_chance": 0.004
        },
    },
    "item_trade_fish_5": {
        "name": "💎 Продажа рыбы V",
        "effect_name": sell_buff_text,
        "price": 9500000,
        "type": "торговля",
        "effect": {
            "trade_type": "fish",
            "trade_multiplier": 75,
            "vanish_chance": 0.005
        },
    },
    "item_trade_mine_5": {
        "name": "💎 Продажа шахты V",
        "effect_name": sell_buff_text,
        "price": 11000000,
        "type": "торговля",
        "effect": {
            "trade_type": "mine",
            "trade_multiplier": 75,
            "vanish_chance": 0.005
        },
    },
    "item_trade_fish_x": {
        "name": "💎 Продажа рыбы (?)",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\n+немного казино\nМожет сломаться",
        "price": 1000000,
        "type": "торговля, казино",
        "effect": {
            "trade_type": "fish",
            "trade_multiplier": 100,
            "vanish_chance": 0.5
        },
    },
    "item_trade_mine_x": {
        "name": "💎 Продажа шахты (?)",
        "effect_name": "Бафф стоимости продажи\n(из хранилища)\n+немного казино\nМожет сломаться",
        "price": 2000000,
        "type": "торговля, казино",
        "effect": {
            "trade_type": "mine",
            "trade_multiplier": 75,
            "vanish_chance": 0.5
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
    "item_double_or_nothing_xp_capsule": {
        "name": "📿 Четки опыта",
        "effect_name": "Double or Nothing\nэффект только на опыт\nБесполезные но дешево\nдля любителей казино",
        "price": 250,
        "type": "капсула, казино",
        "effect": {
            "affected_thing": "xp",
            "double_or_nothing": True
        }
    },
    "item_double_or_nothing_coin_capsule": {
        "name": "💊 Капсула денег",
        "effect_name": "Double or Nothing\nэффект только на деньги\nдля любителей казино",
        "price": 1000,
        "type": "капсула, казино",
        "effect": {
            "affected_thing": "coin",
            "double_or_nothing": True
        }
    },
    "item_double_or_nothing_all_capsule": {
        "name": "💊 К-ла денег и опыта",
        "effect_name": "Double or Nothing\nэффект на опыт и деньги\nдля любителей казино\nопасно в сочетании с другими\n(плохо будет)",
        "price": 3200,
        "type": "капсула, казино",
        "effect": {
            "affected_thing": "xp, coin",
            "double_or_nothing": True
        }
    },
    "item_double_or_nothing_lvl_capsule": {
        "name": "💊 Капсула уровня",
        "effect_name": "Double or Nothing\nэффект только уровень\nдля любителей казино",
        "price": 777666,
        "type": "капсула, казино",
        "effect": {
            "affected_thing": "level",
            "double_or_nothing": True
        }
    }
}



# SHOP_CATEGORIES = get_shop_categories()