


from telegram import Update
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .buttons import get_keyboard
from .type import leaderboard, leaderboard_with_json



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    await query.answer()
    
    pp = "💎 Total PP"
    global_rank = "🌍 Global rank"    
    rank_perc = "(%) Rank"
    country_rank = "🏳️ Country rank"
    total_medals = "🏅 Medals"
    followers = "👥 Followers"
    mapping_followers = "🗺️ Mapping Followers"
    forum_posts = "💬 Forum Posts"
    replays_watched = "🎬 Replays Watched"
    total_score = "📊 Total Score"
    ranked_score = "📈 Ranked Score"
    level = "⭐ Level"
    playcount = "🎮 Playcount"
    hours = "⏱️ Hours"
    avg_count_per_month = "📆 Playcount / Month"
    maps_played = "🗂️ Maps Played"
    accuracy = "🎯 Accuracy"
    hits_per_play = "💥 Hits / Play"
    total_hits = "🔢 Total Hits"
    ssh_ranks = "SS+"
    ss_ranks = "SS"
    sh_ranks = "S+"
    s_ranks = "S"
    a_ranks = "A"
    max_combo = "🔗 Max Combo"

    daily = "⚔️ Дейли челлендж"
    higherlower = "🔰 Higher-Lower"

    count_300 = "300"
    count_100 = "100"
    count_50 = "50"
    count_miss = "❌"
    miss_ratio = "❌ Miss Ratio"

    hits_per_hour = "Hit / Hour"
    minutes_per_play = "Minutes / Play"


    data = query.data
    if ":" not in data:
        await query.edit_message_text("❌ Ошибка")
        return

    prefix, allowed_user_id = data.split(":")
    
    if str(query.from_user.id) != allowed_user_id:
        # await query.edit_message_text("❌ Чужие кнопки")
        return
    
    if prefix.startswith("leaderboard_chat_back"):
        await query.edit_message_text(
            "Топ чата",
            reply_markup=get_keyboard("select_group", allowed_user_id)
        )
        return
    elif prefix.startswith("leaderboard_chat_group_"):
        group = prefix[len("leaderboard_chat_group_"):]
        if group == "profile":
            keyboard = [
                [
                    InlineKeyboardButton(pp, callback_data=f"leaderboard_chat_total_pp:{allowed_user_id}"),
                    InlineKeyboardButton(accuracy, callback_data=f"leaderboard_chat_acc:{allowed_user_id}"),
                ],
                [
                    InlineKeyboardButton(level, callback_data=f"leaderboard_chat_level:{allowed_user_id}"),
                    InlineKeyboardButton(max_combo, callback_data=f"leaderboard_chat_max_combo:{allowed_user_id}"),
                ],
                [
                    InlineKeyboardButton(total_medals, callback_data=f"leaderboard_chat_total_medals:{allowed_user_id}"),
                ],
                [
                    InlineKeyboardButton(hits_per_play, callback_data=f"leaderboard_chat_hpp:{allowed_user_id}"),
                    InlineKeyboardButton(miss_ratio, callback_data=f"leaderboard_chat_miss_ratio:{allowed_user_id}"),
                ]
            ]
        elif group == "plays":
            keyboard = [
                [   
                    InlineKeyboardButton(hours, callback_data=f"leaderboard_chat_hours:{allowed_user_id}"),
                    InlineKeyboardButton(playcount, callback_data=f"leaderboard_chat_playcount:{allowed_user_id}")
                ],
                [                
                    InlineKeyboardButton(maps_played, callback_data=f"leaderboard_chat_maps:{allowed_user_id}"),
                ],
                [
                    InlineKeyboardButton(avg_count_per_month, callback_data=f"leaderboard_chat_avg_count_per_month:{allowed_user_id}"),
                ],
                [
                    InlineKeyboardButton(minutes_per_play, callback_data=f"leaderboard_chat_minutes_per_play:{allowed_user_id}"),
                    InlineKeyboardButton(hits_per_hour, callback_data=f"leaderboard_chat_hits_per_hour:{allowed_user_id}"),
                ]
            ]
        elif group == "social":
            keyboard = [
                [InlineKeyboardButton(forum_posts, callback_data=f"leaderboard_chat_posts:{allowed_user_id}")],
                [InlineKeyboardButton(replays_watched, callback_data=f"leaderboard_chat_replays:{allowed_user_id}")],
                [InlineKeyboardButton(followers, callback_data=f"leaderboard_chat_followers:{allowed_user_id}")],
                [InlineKeyboardButton(mapping_followers, callback_data=f"leaderboard_chat_mapping:{allowed_user_id}")],                
            ]
        elif group == "ranks":
            keyboard = [
                # [InlineKeyboardButton(rank_perc, callback_data=f"leaderboard_chat_rank_perc:{allowed_user_id}")],
                [InlineKeyboardButton(global_rank, callback_data=f"leaderboard_chat_global_rank:{allowed_user_id}")],
                [InlineKeyboardButton(country_rank, callback_data=f"leaderboard_chat_country_rank:{allowed_user_id}")],
                [
                    InlineKeyboardButton(ssh_ranks, callback_data=f"leaderboard_chat_ssh:{allowed_user_id}"),
                    InlineKeyboardButton(sh_ranks, callback_data=f"leaderboard_chat_sh:{allowed_user_id}"),
                ],
                [
                    InlineKeyboardButton(ss_ranks, callback_data=f"leaderboard_chat_ss:{allowed_user_id}"),
                    InlineKeyboardButton(s_ranks, callback_data=f"leaderboard_chat_s:{allowed_user_id}"),
                    InlineKeyboardButton(a_ranks, callback_data=f"leaderboard_chat_a:{allowed_user_id}"),
                ]
            ]
        elif group == "score":
            keyboard = [
                [
                    InlineKeyboardButton(ranked_score, callback_data=f"leaderboard_chat_ranked_score:{allowed_user_id}"),
                    InlineKeyboardButton(total_score, callback_data=f"leaderboard_chat_total_score:{allowed_user_id}"),                    
                ],              
                [
                    InlineKeyboardButton(total_hits, callback_data=f"leaderboard_chat_total_hits:{allowed_user_id}"),
                ],
                [
                    InlineKeyboardButton(count_300, callback_data=f"leaderboard_chat_count_300:{allowed_user_id}"),
                    InlineKeyboardButton(count_100, callback_data=f"leaderboard_chat_count_100:{allowed_user_id}"),
                    InlineKeyboardButton(count_50, callback_data=f"leaderboard_chat_count_50:{allowed_user_id}"),                                        
                    InlineKeyboardButton(count_miss, callback_data=f"leaderboard_chat_count_miss:{allowed_user_id}"),
                ],
            ]
        elif group == "botgames":
            keyboard = [
                [InlineKeyboardButton(daily, callback_data=f"leaderboard_chat_daily:{allowed_user_id}")],
                [InlineKeyboardButton(higherlower, callback_data=f"leaderboard_chat_higherlower:{allowed_user_id}")],
            ]
        else:
            await query.edit_message_text("❌ Неизвестная группа")
            return
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"leaderboard_chat_back:{allowed_user_id}")])


        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"🏆 Выбери...", reply_markup=reply_markup)
        return

    else:
        if ":" in prefix:
            data, allowed_user_id = prefix.split(":", 1)
        else:
            data = prefix
            allowed_user_id = None

        if allowed_user_id and str(query.from_user.id) != allowed_user_id:
            await query.edit_message_text("❌ Чужие кнопки")
            return

        try:
            await query.edit_message_text("<code>/topchat Загрузка...</code>", parse_mode="HTML", reply_markup=None)

            if data == "leaderboard_chat_total_pp":
                await leaderboard(update, context, pp, 'pp', '', 'pp')
            elif data == "leaderboard_chat_rank_perc":
                await leaderboard(update, context, rank_perc, 'rank_perc', '', '%')
            elif data == "leaderboard_chat_global_rank":
                await leaderboard(update, context, global_rank, 'rank', '#', '')
            elif data == "leaderboard_chat_country_rank":
                await leaderboard(update, context, country_rank, 'country_rank', '#', '')
            elif data == "leaderboard_chat_total_medals":
                await leaderboard(update, context, total_medals, 'medals', '', '')
            elif data == "leaderboard_chat_followers":
                await leaderboard(update, context, followers, 'followers', '', '')
            elif data == "leaderboard_chat_mapping":
                await leaderboard(update, context, mapping_followers, 'mapping', '', '')
            elif data == "leaderboard_chat_posts":
                await leaderboard(update, context, forum_posts, 'posts', '', '')
            elif data == "leaderboard_chat_replays":
                await leaderboard(update, context, replays_watched, 'replays', '', '')
            elif data == "leaderboard_chat_total_score":
                await leaderboard(update, context, total_score, 'total_score', '', '')
            elif data == "leaderboard_chat_ranked_score":
                await leaderboard(update, context, ranked_score, 'ranked_score', '', '')
            elif data == "leaderboard_chat_level":
                await leaderboard(update, context, level, 'level', '', '')
            elif data == "leaderboard_chat_playcount":
                await leaderboard(update, context, playcount, 'playcount', '', '')
            elif data == "leaderboard_chat_hours":
                await leaderboard(update, context, hours, 'hours', '', '')
            elif data == "leaderboard_chat_avg_count_per_month":
                await leaderboard(update, context, avg_count_per_month, 'avg_count_per_month', '', '')
            elif data == "leaderboard_chat_maps":
                await leaderboard(update, context, maps_played, 'maps', '', '')
            elif data == "leaderboard_chat_acc":
                await leaderboard(update, context, accuracy, 'acc', '', '')
            elif data == "leaderboard_chat_hpp":
                await leaderboard(update, context, hits_per_play, 'hpp', '', '')
            elif data == "leaderboard_chat_miss_ratio":
                await leaderboard(update, context, miss_ratio, 'miss_ratio', '', '')
            elif data == "leaderboard_chat_hits_per_hour":
                await leaderboard(update, context, hits_per_hour, 'hits_per_hour', '', '')
            elif data == "leaderboard_chat_minutes_per_play":
                await leaderboard(update, context, minutes_per_play, 'minutes_per_play', '', '')
            elif data == "leaderboard_chat_max_combo":
                await leaderboard(update, context, max_combo, 'max_combo', '', '')
            elif data == "leaderboard_chat_total_hits":
                await leaderboard(update, context, total_hits, 'total_hits', '', '')
            elif data == "leaderboard_chat_count_miss":
                await leaderboard(update, context, count_miss, 'count_miss', '', '')
            elif data == "leaderboard_chat_count_300":
                await leaderboard(update, context, count_300, 'count_300', '', '') 
            elif data == "leaderboard_chat_count_100":
                await leaderboard(update, context, count_100, 'count_100', '', '')
            elif data == "leaderboard_chat_count_500":
                await leaderboard(update, context, count_50, 'count_500', '', '')
            elif data == "leaderboard_chat_ssh":
                await leaderboard(update, context, ssh_ranks, 'ssh', '', '')
            elif data == "leaderboard_chat_sh":
                await leaderboard(update, context, sh_ranks, 'sh', '', '')          
            elif data == "leaderboard_chat_ss":
                await leaderboard(update, context, ss_ranks, 'ss', '', '')
            elif data == "leaderboard_chat_s":
                await leaderboard(update, context, s_ranks, 's', '', '')
            elif data == "leaderboard_chat_a":
                await leaderboard(update, context, a_ranks, 'a', '', '')
            elif data == "leaderboard_chat_daily":
                await leaderboard_with_json(update, context, "Daily challenge Leaderboard", "file_daily_challenge")
            elif data == "leaderboard_chat_higherlower":
                await leaderboard_with_json(update, context, "Higher-Lower game Leaderboard", "file_osugames_higherlower")
            else:
                await query.edit_message_text("Неизвестная кнопка!")
            return
        except Exception as e: print (e)
