


from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .....actions.rich import edit_rich_query
from .buttons import get_keyboard
from .type import leaderboard_engine
from .fetch import get_profiles, get_chat_members
from .....external.localapi import read_file_neko


LEADERBOARD_ACTIONS = {
    "leaderboard_chat_total_pp": {
        "title": "💎 PP",
        "prop": "pp",
        "post": "pp",        
    },
    "leaderboard_chat_first_places": {
        "title": "🥇 Первые места",
        "prop": "first_places",
    },
    "leaderboard_chat_global_rank": {
        "title": "🌍 Рейтинг",
        "prop": "rank",
        "pre": "#",
    },
    "leaderboard_chat_country_rank": {
        "title": "🏳️ Рейтинг (страна)",
        "prop": "country_rank",
        "pre": "#",
    },
    "leaderboard_chat_total_medals": {
        "title": "🏅 Медали",
        "prop": "medals",
    },
    "leaderboard_chat_followers": {
        "title": "👥 Подписчики",
        "prop": "followers",
    },
    "leaderboard_chat_mapping": {
        "title": "🗺️ Маппинг подписчики",
        "prop": "mapping",
    },
    "leaderboard_chat_posts": {
        "title": "💬 Форум посты",
        "prop": "posts",
    },
    "leaderboard_chat_replays": {
        "title": "🎬 Просмотры реплеев",
        "prop": "replays",
    },
    "leaderboard_chat_total_score": {
        "title": "📊 Очки (Score)",
        "prop": "total_score",
    },
    "leaderboard_chat_ranked_score": {
        "title": "📈 Рейт. очки",
        "prop": "ranked_score",
    },
    "leaderboard_chat_level": {
        "title": "⭐ Уровень",
        "prop": "level",
    },
    "leaderboard_chat_playcount": {
        "title": "🎮 Игры",
        "prop": "playcount",
    },
    "leaderboard_chat_hours": {
        "title": "⏱️ Плейтайм",
        "prop": "hours",
    },
    "leaderboard_chat_avg_count_per_month": {
        "title": "📆 Игр в месяц",
        "prop": "avg_count_per_month",
    },
    "leaderboard_chat_maps": {
        "title": "🗂️ Карт сыграно",
        "prop": "maps",
    },
    "leaderboard_chat_acc": {
        "title": "🎯 Точность",
        "prop": "acc",
    },
    "leaderboard_chat_hpp": {
        "title": "💥 Hits / Play",
        "prop": "hpp",
    },
    "leaderboard_chat_miss_ratio": {
        "title": "❌ Miss Ratio",
        "prop": "miss_ratio",
    },
    "leaderboard_chat_hits_per_hour": {
        "title": "Попаданий в час",
        "prop": "hits_per_hour",
    },
    "leaderboard_chat_minutes_per_play": {
        "title": "Минут на 1 игру",
        "prop": "minutes_per_play",
    },
    "leaderboard_chat_max_combo": {
        "title": "🔗 Макс. комбо",
        "prop": "max_combo",
        "post": "х",
    },
    "leaderboard_chat_total_hits": {
        "title": "🔢 Всего попаданий",
        "prop": "total_hits",
    },
    "leaderboard_chat_count_miss": {
        "title": "Мисс ❌",
        "prop": "count_miss",
    },
    "leaderboard_chat_count_300": {
        "title": "300 🔵",
        "prop": "count_300",
    },
    "leaderboard_chat_count_100": {
        "title": "100 🟢",
        "prop": "count_100",
    },
    "leaderboard_chat_count_50": {
        "title": "50 🟡",
        "prop": "count_50",
    },
    "leaderboard_chat_ssh": {
        "title": "SS+",
        "prop": "ssh",
    },
    "leaderboard_chat_sh": {
        "title": "S+",
        "prop": "sh",
    },
    "leaderboard_chat_ss": {
        "title": "SS",
        "prop": "ss",
    },
    "leaderboard_chat_s": {
        "title": "S",
        "prop": "s",
    },
    "leaderboard_chat_a": {
        "title": "A",
        "prop": "a",
    },    
    "leaderboard_chat_daily": {
        "title": "⚔️ Дейли челлендж",
        "provider": "file_daily_challenge",
        "post": "pts",
    },
    "leaderboard_chat_higherlower": {
        "title": "🔰 Higherlower игра",
        "provider": "file_osugames_higherlower",
        "post": "pts",
    },
    "leaderboard_chat_ecos": {
        "title": "🕯 Экономика",
        "provider": "ecos"
    },
    "leaderboard_chat_nish": {
        "title": "🕳 Нишевость",
        "prop": "top_100_nish",
        "post": "%",
    },
    "leaderboard_chat_ppfire": {
        "title": "🔥 Костер РР",
        "prop": "top_100_ppfire",
        "post": "pp",
    },
    "leaderboard_chat_anime": {
        "title": "🎀 Аниме фоны",
        "prop": "top_100_anime",
        "post": "%",
    },
    "leaderboard_chat_aimslop": {
        "title": "🎯 Аим слоп",
        "prop": "top_100_aimslop",
        "post": "pp",
    },
    "leaderboard_chat_speedslop": {
        "title": "🚙 Спид слоп",
        "prop": "top_100_speedslop",
        "post": "pp",
    },
    "leaderboard_chat_skill_speed": {
        "title": "🔺 Speed",
        "extra_title": "(карточка /skills)",
        "prop": "top_100_skill_speed",
    },
    "leaderboard_chat_skill_aim": {
        "title": "🔺 Aim",
        "extra_title": "(карточка /skills)",
        "prop": "top_100_skill_aim",
    },
    "leaderboard_chat_skill_accuracy": {
        "title": "🔺 Acc.",
        "extra_title": "(карточка /skills)",
        "prop": "top_100_skill_accuracy",
    },
    "leaderboard_chat_skill_all": {
        "title": "💱 Все скиллы (карточка /skills)",
        "prop": "top_100_skill_all",
    },
}

GROUPS = {
    "profile": [
        ["leaderboard_chat_total_pp", "leaderboard_chat_acc"],
        ["leaderboard_chat_level", "leaderboard_chat_max_combo"],
        ["leaderboard_chat_total_medals"],
        ["leaderboard_chat_hpp", "leaderboard_chat_miss_ratio"],
    ],
    "plays": [
        ["leaderboard_chat_hours", "leaderboard_chat_playcount"],
        ["leaderboard_chat_maps"],
        ["leaderboard_chat_avg_count_per_month"],
        ["leaderboard_chat_minutes_per_play", "leaderboard_chat_hits_per_hour"],
    ],
    "social": [
        ["leaderboard_chat_posts"],
        ["leaderboard_chat_replays"],
        ["leaderboard_chat_followers"],
        ["leaderboard_chat_mapping"],
    ],
    "ranks": [
        ["leaderboard_chat_global_rank"],
        ["leaderboard_chat_country_rank"],
        ["leaderboard_chat_ssh", "leaderboard_chat_sh"],
        ["leaderboard_chat_ss", "leaderboard_chat_s", "leaderboard_chat_a"],
        ["leaderboard_chat_first_places"],
    ],
    "score": [
        ["leaderboard_chat_ranked_score", "leaderboard_chat_total_score"],
        ["leaderboard_chat_total_hits"],
        ["leaderboard_chat_count_300", "leaderboard_chat_count_100"],
        ["leaderboard_chat_count_50", "leaderboard_chat_count_miss"],
    ],
    "botgames": [
        ["leaderboard_chat_daily"],
        ["leaderboard_chat_higherlower"],
        ["leaderboard_chat_ecos"],
    ],
    "top100": [
        ["leaderboard_chat_ppfire"],         
        ["leaderboard_chat_aimslop", "leaderboard_chat_speedslop"],
        ["leaderboard_chat_anime", "leaderboard_chat_nish"],    
        ["leaderboard_chat_skill_all"], 
        ["leaderboard_chat_skill_speed", "leaderboard_chat_skill_aim", "leaderboard_chat_skill_accuracy"],
    ]
}

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if ":" not in data:
        return await query.answer("err 1", show_alert=True)

    prefix, allowed_user_id = data.split(":")
    if str(query.from_user.id) != allowed_user_id:
        return

    if prefix.startswith("leaderboard_chat_back"):
        
        reply_markup=get_keyboard("select_group", allowed_user_id)      
        text = "### 🏆 Топ чата <code> - выбeри раздел</code>"               
        
        await edit_rich_query(
            query,
            markdown=text,
            reply_markup=reply_markup
        )  
        return

    if prefix.startswith("leaderboard_chat_group_"):
        group = prefix.replace("leaderboard_chat_group_", "")

        if group not in GROUPS:
            return await query.answer("err 2", show_alert=True)

        keyboard = [
            [
                InlineKeyboardButton(
                    LEADERBOARD_ACTIONS[key]["title"],
                    callback_data=f"{key}:{allowed_user_id}"
                )
                for key in row
            ]
            for row in GROUPS[group]
        ]

        keyboard.append([
            InlineKeyboardButton("⬅️ Назад",
                                 callback_data=f"leaderboard_chat_back:{allowed_user_id}")
        ])

        reply_markup=InlineKeyboardMarkup(keyboard)        
        text = "### 🏆 Топ чата <code> - выбери ...</code>"               
        
        await edit_rich_query(
            query,
            markdown=text,
            reply_markup=reply_markup
        )

        return

    action = LEADERBOARD_ACTIONS.get(prefix)

    if not action:
        return await query.answer("err 3", show_alert=True)

    await edit_rich_query(
        query,
        markdown="### <code>Загрузка...</code>"
    )    

    provider_data = await get_provider(action.get("provider", "profiles"), update, context)

    await leaderboard_engine(
        query,
        action=action,
        raw_data=provider_data,        
    )

async def get_provider(name, update, context):
    if name == "profiles":
        return await get_profiles(update, context)

    if name.startswith("file_"):
        data = await read_file_neko(name)
        return {
            "data": data.get("current", {}),
            "members": await get_chat_members(update, context),
        }
    
    if name.startswith("ecos"):
        return {
            "members": await get_chat_members(update, context),
            # "profiles": await get_profiles(update, context)
        }

    raise ValueError("Unknown provider")