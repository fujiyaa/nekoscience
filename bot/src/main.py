
from config import *
import bot.src.modules.external.localapi as localapi
import bot.src.modules.systems.auth as auth

def mark_group_progress():
    for fname in os.listdir(GROUPS_DIR):
        if not fname.endswith(".todo"):
            continue

        group_id = fname.split(".")[0]
        todo_path = os.path.join(GROUPS_DIR, fname)
        done_path = os.path.join(GROUPS_DIR, f"{group_id}.done")

        if os.path.exists(done_path):
            continue

        with open(todo_path, "r", encoding="utf-8") as f:
            targets = [line.strip() for line in f if line.strip()]

        all_ready = all(os.path.exists(path) for path in targets)

        if all_ready:
            os.rename(todo_path, done_path) 
            print(f"✅ Группа {group_id} завершена!")
 
#mods&mappers cmd TODO add single api req
async def start_mappers(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(mappers(update, context, user_request))
async def mappers(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="mappers",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return

    MAX_ATTEMPTS = 3

    user_id = str(update.message.from_user.id)
    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/mappers fujina123` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        "`Загрузка...`", parse_mode="Markdown"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Игрок не найден`",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_pp = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_pp = []
                print(e)

            
            if isinstance(best_pp, list) and best_pp:
                

                mapper_counter = defaultdict(lambda: {"pp_sum": 0.0, "count": 0})

                for score in best_pp:
                    mapper = score.get("mapper", "Unknown")
                    raw_pp = score.get("pp", 0.0) or 0.0

                    if "weight_percent" in score:
                        weighted_pp = raw_pp * (score["weight_percent"] / 100.0)
                    else:
                        weighted_pp = raw_pp

                    mapper_counter[mapper]["pp_sum"] += weighted_pp
                    mapper_counter[mapper]["count"] += 1

                sorted_mappers = sorted(
                    mapper_counter.items(),
                    key=lambda x: (x[1]["count"], x[1]["pp_sum"]),
                    reverse=True
                )

                top_mappers = sorted_mappers[:10]

                mapper_width = max(len(mapper) for mapper, _ in top_mappers) if top_mappers else 0
                pp_width = max(len(f"{data['pp_sum']:.2f}") for _, data in top_mappers) if top_mappers else 0
                count_width = max(len(str(data['count'])) for _, data in top_mappers) if top_mappers else 0

                table_lines = [
                    f"{'Mapper':<{mapper_width}} | {'PP':>{pp_width}} | {'#':>{count_width}}",
                    f"{'-'*mapper_width}-+-{'-'*pp_width}-+-{'-'*count_width}"
                ]
                for mapper, data in top_mappers:
                    table_lines.append(
                        f"{mapper:<{mapper_width}} | {data['pp_sum']:>{pp_width}.2f} | {data['count']:>{count_width}}"
                    )

                table_text = "\n".join(table_lines)

                username = user_data["username"]
                stats = user_data["statistics"]
                pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
                global_rank_text = f"(#{stats.get('global_rank'):,}" if stats.get("global_rank") else "(#????"
                country_rank_text = (
                    f"  {user_data['country_code']}#{stats.get('country_rank'):,})"
                    if stats.get("country_rank") else f"  {user_data['country_code']}#???)"
                )
                rank_text = f"{username}: {pp_text}pp {global_rank_text}{country_rank_text}"
                country_flag = country_code_to_flag(user_data["country_code"])

                user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
                user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'

                text = f"{user_link}\n\n<pre>{table_text}</pre>"
                
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML"
                    )
                    return
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML"
                    )
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных или ошибка сети")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при mappers (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
async def start_mods(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(mods(update, context, user_request))               
async def mods(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="mods",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3

    user_id = str(update.message.from_user.id)
    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/mods fujina123` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        "`Загрузка...`", parse_mode="Markdown"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Игрок не найден`",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_pp = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_pp = "N/A"
                print(e)


            if isinstance(best_pp, list) and best_pp:
                mod_counter = Counter()
                combo_counter = Counter()
                # combo_pp_sum = defaultdict(float)
                combo_pp_weighted_sum = defaultdict(float)

                for score in best_pp:
                    mods = score.get("mods", [])
                    combo = format_mods(mods)

                    if mods:
                        for m in mods:
                            mod_counter[m] += 1
                    else:
                        mod_counter["NM"] += 1

                    combo_counter[combo] += 1

                    pp_value = score.get("pp", 0.0) or 0.0
                    weight_percent = score.get("weight_percent", 0.0) or 0.0

                    # combo_pp_sum[combo] += pp_value
                    combo_pp_weighted_sum[combo] += pp_value * (weight_percent / 100)

                total_scores = len(best_pp)

                fav_mods_str = format_blocks_percent(mod_counter, total_scores, per_row=4)
                fav_combos_str = format_blocks_percent(combo_counter, total_scores, per_row=3)
                # profit_combos_str = format_blocks_pp(combo_pp_sum, per_row=3)
                weighted_combos_str = format_blocks_pp(combo_pp_weighted_sum, per_row=3)

                username = user_data["username"]                
                stats = user_data["statistics"]

                pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
                global_rank_text = f"(#{stats.get('global_rank'):,}" if stats.get("global_rank") else "(#????"
                country_rank_text = (
                    f"  {user_data['country_code']}#{stats.get('country_rank'):,})"
                    if stats.get("country_rank") else f"  {user_data['country_code']}#???)"
                )

                rank_text = f"{username}: {pp_text}pp {global_rank_text}{country_rank_text}"
                country_flag = country_code_to_flag(user_data["country_code"])

                user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
                user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'                
               
                text = (
                    f"{user_link}\n\n"
                    "⦿ <b><u>Top100 mods:</u></b>\n\n"
                    f"<b>Favourite mods</b>\n{fav_mods_str}\n\n"
                    f"<b>Favourite mod combinations</b>\n{fav_combos_str}\n\n"
                    # f"<b>Profitable mod combinations (pp)</b>\n{profit_combos_str}\n\n"
                    f"<b>Profitable mod combinations (pp)</b>\n{weighted_combos_str}"
                )

                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML"
                    )
                    return
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML"            
                )
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных по топ-100.")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при mods (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )

#pc cmd TODO add single arg 
async def start_compare_profile(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(compare_profile(update, context, user_request))
async def compare_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="pc",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return
    
    MAX_ATTEMPTS = 3  
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            temp_message = await update.message.reply_text(f"`Загрузочка... `{attempt}/{MAX_ATTEMPTS}", parse_mode="Markdown") 
            break
        except Exception as e:
            print(e)
            return

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
    
            await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Загрузочка... {attempt}/{MAX_ATTEMPTS}`", 
                    parse_mode="Markdown")

            args_text = " ".join(context.args)

            if args_text.count("#") == 1:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Ошибка: найден только один #. Должно быть либо 0, либо 2.`",
                    parse_mode="Markdown"
                )
                return
            elif args_text.count("#") == 2:
                parts = args_text.split("#")
                username1 = parts[1].strip()
                username2 = parts[2].strip()
            else:
                parts = args_text.split()
                if len(parts) != 2:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=(
                            "Использование: `/pc <ник1> <ник2>`\n\n"
                            "Пример: `/pc Fujiya Vaxei`\n"
                            "Или с пробелами: `/pc #Fujiya #cs Pro 2014`"
                        ),
                        parse_mode="Markdown"
                    )
                    return
                username1, username2 = parts[0], parts[1]
            
            token = await get_osu_token()
            async def fetch_data(name):
                try:
                    user_data = await asyncio.wait_for(get_user_profile(name, token=token), timeout=10)
                    user_id = user_data["id"]
                    best_pp = await asyncio.wait_for(get_top_100_scores(name, token, user_id), timeout=10)
                    return user_data, best_pp
                except:
                    return None, None

            user1, top1 = await fetch_data(username1)
            user2, top2 = await fetch_data(username2)

            if not user1 or not user2:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Что-то пошло не так...`",
                    parse_mode="Markdown"
                )
                return
           
            p1 = format_stats(user1, top1)
            p2 = format_stats(user2, top2)

            header, sep = make_header(p1['name'], p2['name'])
            table = [header, sep]

            table.append(row(p1['rank'], "Rank", p2['rank'], higher_is_better=False, preffix="#", fmt="{:,}"))
            table.append(row(p1['peak_rank'], "Peak rank", p2['peak_rank'], higher_is_better=False, preffix="#", fmt="{:,}"))
            table.append(row(p1['pp'], "PP", p2['pp'], higher_is_better=True, suffix="pp", fmt="{:,.0f}"))
            table.append(row(p1['acc'], "Accuracy", p2['acc'], higher_is_better=True, suffix="%", fmt="{:,.2f}"))
            table.append(row(p1['level'], "Level", p2['level'], higher_is_better=True, fmt="{:.2f}"))
            table.append(row(p1['hours'], "Playtime", p2['hours'], higher_is_better=True, suffix="hrs", fmt="{:,}"))
            table.append(row(p1['playcount'], "Playcount", p2['playcount'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['max_count'], "PC peak", p2['max_count'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['maps'], "Maps played", p2['maps'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['ranked_score']/1e9, "Ranked score", p2['ranked_score']/1e9, higher_is_better=True, suffix="bn", fmt="{:.2f}"))
            table.append(row(p1['total_score']/1e9, "Total score", p2['total_score']/1e9, higher_is_better=True, suffix="bn", fmt="{:.2f}"))
            table.append(row(p1['total_hits'], "Total hits", p2['total_hits'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['hpp'], "Hits/play", p2['hpp'], higher_is_better=True, fmt="{:,.2f}"))
            table.append(row(p1['ss'], "SS count", p2['ss'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['s'], "S count", p2['s'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['a'], "A count", p2['a'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['max_combo'], "Max Combo", p2['max_combo'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['medals'], "Medals", p2['medals'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['top1_pp'], "Top1 PP", p2['top1_pp'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['pp_diff'], "PP spread", p2['pp_diff'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['pp_avg_all'], "Avg PP", p2['pp_avg_all'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['avg_pp_per_month'], "PP per month", p2['avg_pp_per_month'], higher_is_better=True, suffix="pp", fmt="{:,.2f}"))
            table.append(row(p1['avg_count_per_month'], "PC per month", p2['avg_count_per_month'], higher_is_better=True, fmt="{:,.0f}"))
            table.append(row(p1['join_date'], "Join date", p2['join_date'], higher_is_better=False, is_date=True))
            table.append(row(p1['followers'], "Followers", p2['followers'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['mapping'], "Mapping subs", p2['mapping'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['posts'], "Forum posts", p2['posts'], higher_is_better=True, fmt="{:,}"))
            table.append(row(p1['replays'], "Replays seen", p2['replays'], higher_is_better=True, fmt="{:,}"))

            text = "```\n" + "\n".join(table) + "\n```"

            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=temp_message.message_id,
                text=text,
                parse_mode="Markdown"
            )
            return
        
        except Exception as e:
            print(f"Ошибка при pc (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )
#fix cmd TODO add index arg 
async def start_recent_fix(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(recent_fix(update, context, user_request))
async def recent_fix(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="recent_fix",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_RECENT_FIX_COMMAND,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_RECENT_FIX_COMMAND} секунд"
        )
    if not can_run:
        return

    try:
        uid = update.effective_user.id
        saved_name = await auth.check_osu_verified(str(uid))

        if context.args:
            username = " ".join(context.args)
        elif saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/fix Fujiya` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
     
        text = "`загрузка...`"
        
        loading_msg = await try_send(update.message.reply_text, text, parse_mode="Markdown")

        token = await get_osu_token()
        scores = await get_user_scores(username, token, limit=1)

        if not scores:
            await safe_send_message(update, text="❌ Нет последних игр", parse_mode="Markdown")
            await loading_msg.delete()
            return

        score = scores[0]
        
        msg = await try_send(send_score_fix, update, score, uid, token)
        await loading_msg.delete()

      
        
    except Exception:
        traceback.print_exc()
async def send_score_fix(update, score, user_id, token:str = None):    
    
    path, base_values = await beatmap(score['beatmap']['id'])    
    score_stats = score.get("score_stats", score.get("statistics")) 

    base_ar = score.get("DA_values", {}).get("approach_rate", base_values["ar"])
    base_cs = score.get("DA_values", {}).get("circle_size", base_values["cs"])
    base_od = score.get("DA_values", {}).get("overall_difficulty",base_values["od"])
    base_hp = score.get("DA_values", {}).get("drain_rate", base_values["hp"])          
    
    #neko API 
    payload = {
        "map_path": str(score['beatmap']['id']), 
        
        "n300": score_stats.get("count_300", None),
        "n100": score_stats.get("count_100", None),
        "n50": score_stats.get("count_50", None),
        "misses": int(score['count_miss']),                   
        
        "mods": str(score.get("mods", 0)), 
        "combo": int(score['max_combo']),      
        "accuracy": float(score['accuracy']*100),    
        
        "lazer": bool(score.get('lazer', False)),          
        "clock_rate": float(score.get('speed_multiplier') or 1.0),  

        "custom_ar": float(base_ar),
        "custom_cs": float(base_cs),
        "custom_hp": float(base_hp),
        "custom_od": float(base_od),
    }

    try:
        pp_data = await localapi.get_score_pp_neko_api(payload)

        pp = pp_data.get("pp")
        max_pp = pp_data.get("no_choke_pp")
        perfect_pp = pp_data.get("perfect_pp")

        stars = pp_data.get("star_rating")
        perfect_combo = pp_data.get("perfect_combo")
        expected_bpm = pp_data.get("expected_bpm")

    except Exception as e:
        print(f"neko API failed: {e}")
    
    
    mods_str = score.get("mods", "")
    mods_text = normalize_no_plus(mods_str)
    try:
        best_pp = await asyncio.wait_for(get_top_100_scores(score['user']['username'], token, score['user']['id']), timeout=10, )        
    except:
        return

    live_raw_pp = calculate_weighted_pp(best_pp, bonus_pp=0)
    map_pp = float(f"{max_pp:.3f}")

    try:
        pos, new_best_pp  = insert_pp(best_pp, map_pp, '')
    except:
        pos = None

    username = score['user']['username']
    total_pp, global_rank, country_rank, country_code = score['total_pp'], score['global_rank'], score['country_rank'], score['country_code']
    pp_text = f"{total_pp}"
    country_rank_text = (
        f"  {country_code}#{country_rank:,})"
    )
    rank_text = f"{username}: {pp_text}pp (#{global_rank}{country_rank_text}"
    country_flag = country_code_to_flag(country_code)
    user_link = f'{country_flag} <b>{rank_text}</b>'  

    pp_int, pp_frac = str(f"{pp:.2f}").split(".")
    max_pp_int, max_pp_frac = str(f"{max_pp:.2f}").split(".")
    
    s = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(user_id), {}) 
    lang_code = user_settings.get("lang", "ru")   

    
    if pos is not None and pos<101:
        live_pp = total_pp
        bonus =  float(live_pp) - float(live_raw_pp)
        if bonus < 0: bonus = 0

        new_total = calculate_weighted_pp(new_best_pp, bonus)
        best_text =(
            f"{TR['r_fix_it_would'][lang_code]}<b>#{pos+1}</b>{TR['r_fix_in_top_100'][lang_code]}<b>{new_total:.2f}pp</b>."
        )    
    else:
        best_text =(
            f"\n{TR['r_fix_top100'][lang_code]}."
        ) 

    caption = (
        f"{user_link}\n\n"
        f'{mods_text} <b>FC</b>{TR["r_fix_improve"][lang_code]}<a href="{score["url"]}">{TR["r_fix_the_score"][lang_code]}</a>'
        f"{TR['r_fix_from'][lang_code]}<u>{pp_int}</u>.{pp_frac} "
        f"{TR['r_fix_to'][lang_code]}<b><u>{max_pp_int}</u>.{max_pp_frac}рр</b>.{best_text}"
        f"\n⠀"
    )        
    
    return await update.message.reply_text(text=caption, parse_mode="HTML")

#beatmaps cmd TODO add watch another ppl arg 


async def beatmaps_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_name = query.from_user.username
    action, owner_id = query.data.split(":")
    owner_id = int(owner_id)

    if action == "beatmaps_refresh":
        if not os.path.exists(FLAG_FILE):
            open(FLAG_FILE, "w").close()
            asyncio.create_task(worker())
            print("worker startup from query")

        msg, reply_markup = await build_beatmaps_text(owner_id)
        
        try:
            await query.edit_message_text(
                msg,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except BadRequest as e:
            if "Message is not modified" in str(e):
                await safe_query_answer(query,"🍉 Ничего нового...")
            else:
                raise
        return
    
    if user_id != owner_id:
        await safe_query_answer(query,"⛔ Чужая кнопка")
        return
    
    if action == "beatmaps_count_me":
        count_me_times = temp.load_json(COUNT_ME_FILE, default={})
        now = time.time()
        last_click = count_me_times.get(str(user_id), 0)

        if now - last_click < COOLDOWN_WEEK_SECONDS:
            remaining = COOLDOWN_WEEK_SECONDS - (now - last_click)
            days = int(remaining // 86400)
            hours = int((remaining % 86400) // 3600)
            await safe_query_answer(query, f"⏳ Подождите ещё {days} д {hours} ч, прежде чем нажимать снова.")
            return        
        
        saved_name = await auth.check_osu_verified(str(update.effective_user.id))
                
        if saved_name is None:
            await safe_query_answer(query, "🚷 Сначала нужно сохранить имя /name...")     
            return       
        else:
            await safe_query_answer(query, "👍 Запуск... \nНажми кнопку ОБНОВИТЬ чтобы увидеть статус")

        count_me_times[str(user_id)] = now
        temp.save_json(COUNT_ME_FILE, count_me_times)

        try:            
            group_state = await check_group_status(user_id)

            if group_state == 'not_found':
                pass
            
            elif group_state == 'done':
                print('query recalculating existing user, deleting data...')
                await delete_done_file(user_id)
            
            else:
                raise ValueError("group_state == in_progress")   

            token = await get_osu_token()
            best_pp = await asyncio.wait_for(get_top_100_scores(saved_name, token=token), timeout=10)
            if best_pp is None:              
                if update and context:                                          
                    warn_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Такого ника не существует...",
                        message_thread_id=getattr(update.message, "message_thread_id", None)
                    )
                    asyncio.create_task(delete_message_after_delay(context, warn_msg.chat_id, warn_msg.message_id, 5))                
                raise ValueError("best_pp is None")
            
            most_played = await asyncio.wait_for(get_most_played(saved_name, token=token), timeout=10)
            if most_played is None:              
                if update and context:                                          
                    warn_msg = await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Такого ника не существует...",
                        message_thread_id=getattr(update.message, "message_thread_id", None)
                    )
                    asyncio.create_task(delete_message_after_delay(context, warn_msg.chat_id, warn_msg.message_id, 5))                
                raise ValueError("best_pp is None")
           
            for score in best_pp:
                await addtask(
                    url = score.get("beatmap_url"),
                    task = 'beatmap_data',
                    group_id = user_id
            )
            for map in most_played:
                await addtask(
                    url = map.get("beatmap_url"),
                    task = 'beatmap_data',
                    group_id = user_id
            )
        
        except Exception as e:
            print(f"query adding workers: {e}")

            if str(e) != "group_state == in_progress":
                try:
                    count_me_times = temp.load_json(COUNT_ME_FILE, default={})
                    if str(user_id) in count_me_times:
                        del count_me_times[str(user_id)]
                        temp.save_json(COUNT_ME_FILE, count_me_times)
                        print(f"Cooldown for user {user_id} removed due to error.")
                except Exception as ex:
                    print(f"Error while removing cooldown: {ex}")

        finally:
            print(f"query adding workers done")

           
    elif action.startswith("beatmaps_stats"):
        sub_action = action.replace("beatmaps_stats", "").strip("_") or "200"

        todo_file = os.path.join(GROUPS_DIR, f"{user_id}.todo")
        done_file = os.path.join(GROUPS_DIR, f"{user_id}.done")

        if os.path.exists(todo_file):
            await safe_query_answer(query, "⏳ Ещё не готово!!!!!!!")
            return
        elif not os.path.exists(done_file):
            await safe_query_answer(query, "🚷 Еще нет статистики, может быть нажать на звездочку?")
            return

        try:            
            
            def filter_tags(tags, blacklist):
                return [t for t in tags if t.lower() not in blacklist]

            def format_top(counter, title, top_n=9, max_bar_width=5):
                most_common = counter.most_common(top_n)
                other_count = sum(count for _, count in counter.items()) - sum(count for _, count in most_common)

                split_tags = [t[0].split("/", 1) + [t[1]] if "/" in t[0] else [t[0], "", t[1]] for t in most_common]

                max_first_len = max(len(first) for first, _, _ in split_tags + [("other", "", 0)])
                max_second_len = max(len(second) for _, second, _ in split_tags + [("","",0)])

                max_count = max(count for _, _, count in split_tags) if split_tags else 1

                lines = []
                for first, second, count in split_tags:
                    bar_len = int((count / max_count) * max_bar_width)
                    bar_len = max(bar_len, 1)
                    bar = "▇" * bar_len
                    lines.append(f"{first.ljust(max_first_len)}  {second.ljust(max_second_len)} {bar} {count}")

                lines.append(f"{'other'.ljust(max_first_len)}  {'':{max_second_len}} {other_count}")
                return lines

            with open(done_file, "r", encoding="utf-8") as f:
                beatmap_paths = [line.strip() for line in f if line.strip()]

            if sub_action == "1_100":
                beatmap_paths = beatmap_paths[:100]
                title_text = "🔹 top-100 pp" 
            elif sub_action == "101_200":
                beatmap_paths = beatmap_paths[100:200]                 
                title_text = "🔸 most played"  
            else:  
                beatmap_paths = beatmap_paths[:200]  
                title_text = "📊 200 карт"     

            related_tag_counter = Counter()
            tags_counter = Counter()
            genre_counter = Counter()
            language_counter = Counter()
            artist_counter = Counter()


            for path in beatmap_paths:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as bf:
                        try:
                            data = json.load(bf)
                        except json.JSONDecodeError:
                            continue 

                        if isinstance(data, dict):
                            related_tags = data.get("related_tags", [])
                            related_tag_counter.update(related_tags)

                            TAGS_FILTER = {
                                "the","of", "to","a","no", "wa","tv",                               
                                "english", "japanese", "russian", "korean",                               
                                "version",
                                "featured", "artist",   
                                }
                            tags = data.get("tags", [])
                            if isinstance(tags, str):
                                tags = tags.split()
                            tags = filter_tags(tags, TAGS_FILTER)
                            tags_counter.update(tags)

                            genre = data.get("genre")
                            if genre:
                                genre_counter.update([genre])

                            language = data.get("language")
                            if language:
                                language_counter.update([language])

                            artist = data.get("artist")
                            if artist:
                                artist_counter.update([artist])

                        elif isinstance(data, list):
                            tags_counter.update(data)

            if not related_tag_counter and not tags_counter:
                await safe_query_answer(query, "⚠️ Нет тегов в картах.")
                return

            saved_name = await auth.check_osu_verified(str(update.effective_user.id))
            saved_name = html.escape(saved_name)

            related_lines = format_top(related_tag_counter, "related_tags")
            tags_lines = format_top(tags_counter, "обычные tags")
            artist_lines = format_top(artist_counter, "исполнители")

            all_lines = []
            all_lines.append(f"{title_text} 🏷 Юзертеги: {saved_name}") 
            all_lines.append("────────────────────────────")
            all_lines.extend(related_lines)
            all_lines.append("────────────────────────────")
            all_lines.append(f"🏷 Теги, добавленные маппером:")
            all_lines.extend(tags_lines)
            all_lines.append("────────────────────────────")
            all_lines.append(f"🏷 Топ исполнителей:")
            all_lines.extend(artist_lines)
            all_lines.append("────────────────────────────")

            top_genre = html.escape(genre_counter.most_common(1)[0][0]) if genre_counter else "—"
            top_language = html.escape(language_counter.most_common(1)[0][0]) if language_counter else "—"
            all_lines.append(f"✳️ Любимый жанр: {top_genre}")
            all_lines.append(f"🌐 Любимый язык: {top_language}")

            table_text = "<pre>" + html.escape("\n".join(all_lines)) + "</pre>"

            if update and context:
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=update.callback_query.message.message_id,
                        text=table_text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Ошибка редактирования сообщения: {e}")
        except Exception as e:
            print(f"Ошибка обработки beatmaps_stats: {e}")
            await safe_query_answer(query, f"❌ Произошла неизвестная ошибка. \n\n{e}")
async def worker():
    await asyncio.sleep(1)
    try:
        processed = 0

        while True:
            if not os.path.exists(QUEUE_FILE):
                break

            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            if not lines:
                break

            task_line = lines[0]
            parts = task_line.split(" ")
            url, task, group_id = parts[0], parts[1], parts[2]

            skip_timeout = False 

            if task == "beatmap_data":
                file_id = url.split("/")[-1]
                out_file = os.path.join(STATS_BEATMAPS, f"{file_id}.json")

                if os.path.exists(out_file):
                    print(f"⏭️ Already exists: {out_file}, skipping download...")
                    skip_timeout = True
                else:
                    print(f"🔄 Loading: {url}")
                    data = await fetch_beatmap_data(url)
                    with open(out_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    print(f"✅ Saved {out_file}")

            with open(QUEUE_FILE, "w", encoding="utf-8") as f:
                f.writelines(line + "\n" for line in lines[1:])

            processed += 1

            if processed % 25 == 0 or not lines[1:]:
                mark_group_progress()

            if os.path.exists(QUEUE_FILE) and lines[1:]:
                if skip_timeout:
                    print("⚡ Skipped timeout (cached file)")
                else:
                    await asyncio.sleep(URL_SCAN_TIMEOUT)

    except Exception as e:
        print(e)
        mark_group_progress() 
    finally:
        mark_group_progress()         
        if os.path.exists(FLAG_FILE):
            os.remove(FLAG_FILE)
        print("worker job done")
async def addtask(url, task, group_id):
    file_id = url.split("/")[-1]
    out_file = os.path.join(STATS_BEATMAPS, f"{file_id}.json")

    with open(QUEUE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{url} {task} {group_id}\n")

    with open(os.path.join(GROUPS_DIR, f"{group_id}.todo"), "a", encoding="utf-8") as f:
        f.write(out_file + "\n")

    print(f"📌 Добавил задачу: {url} ({task}), группа {group_id}")

    if not os.path.exists(FLAG_FILE):
        open(FLAG_FILE, "w").close()
        asyncio.create_task(worker())
        print("▶️ Запустил воркер")
async def check_group_status(group_id: str) -> str:
    """
    Проверяет статус группы по group_id.
    Возвращает:
      - "not_found"  → если нет такого файла
      - "in_progress" → если есть .todo, но нет .done
      - "done"       → если есть .done
    """
    todo_path = os.path.join(GROUPS_DIR, f"{group_id}.todo")
    done_path = os.path.join(GROUPS_DIR, f"{group_id}.done")

    if not os.path.exists(todo_path) and not os.path.exists(done_path):
        return "not_found"
    elif os.path.exists(done_path):
        return "done"
    else:
        return "in_progress"
async def delete_done_file(group_id: str):
    """
    Удаляет файл группы с расширением .done, если он существует.
    """
    done_path = os.path.join(GROUPS_DIR, f"{group_id}.done")

    if os.path.exists(done_path):
        try:
            os.remove(done_path)
            print(f"✅ Файл {group_id}.done успешно удалён.")
        except Exception as e:
            print(f"❌ Ошибка при удалении файла {group_id}.done: {e}")
    else:
        print(f"⚠️ Файл {group_id}.done не найден.")

#simulate cmd



#settings cmd
async def settings_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await log_all_update(update)

    user_id = str(update.effective_user.id)
    name = str(update.effective_user.name)

    settings = temp.load_json(USER_SETTINGS_FILE, default={})
  
    kb, text = await get_settings_kb(user_id, settings)

    await update.message.reply_text(
        f'{text} {name}',
        reply_markup=InlineKeyboardMarkup(kb)
    )
async def settings_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    name = str(query.from_user.name)
    action, owner_id = query.data.split(":")

    if user_id != owner_id:
        await safe_query_answer(query, "Чужая кнопка") 
        return

    settings = temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = settings.get(str(user_id), {"lang": "ru", "notify": True, "rs_bg_render": False, "new_card": True})    

    if action == "settings_english":
        user_settings["lang"] = "en"
        await safe_query_answer(query) 

    elif action == "settings_russian":
        user_settings["lang"] = "ru"
        await safe_query_answer(query) 

    elif action == "settings_rs_bg_yes":
        user_settings["rs_bg_render"] = True
        await safe_query_answer(query) 

    elif action == "settings_rs_bg_no":
        user_settings["rs_bg_render"] = False
        await safe_query_answer(query) 

    elif action == "settings_new_card":
        user_settings["new_card"] = True
        await safe_query_answer(query) 

    elif action == "settings_old_card":
        user_settings["new_card"] = False
        await safe_query_answer(query) 

    elif action == "settings_ignore":
        await safe_query_answer(query) 

    settings[user_id] = user_settings
    temp.save_json(USER_SETTINGS_FILE, settings)

    kb, text = await get_settings_kb(user_id, settings)

    try:
        await query.edit_message_text(
            f'{text} {name}',
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except Exception as e:
        await query.answer()



#testing zone

async def start_nochoke(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(nochoke(update, context, user_request))
async def nochoke(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="average_stats",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 1  

    user_id = str(update.message.from_user.id)
    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    miss_limit = None
    args = context.args

    if args:
        # %N
        for arg in args:
            if arg.startswith("%") and arg[1:].isdigit():
                miss_limit = int(arg[1:])
                args.remove(arg)
                break
        username = " ".join(args) if args else saved_name
    else:
        username = saved_name

    if not username:
        text = (f"`Нужна помощь?`\n\n"
                f"Сохранить ник: */name*\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n"
        )
        await safe_send_message(update, text, parse_mode="Markdown")
        return

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        text=f"`Загрузочка... (20 сек макс.)`\n\n"
                        f"Сохраненный ник: *{saved_name}*\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n", parse_mode="Markdown"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Нет игрока или статистики...`\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_scores = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_scores = "N/A"
                print(e)            
            

            if isinstance(best_scores, list) and best_scores:
                live_raw_pp = calculate_weighted_pp(best_scores, bonus_pp=0)
                                
                stats = user_data["statistics"]
                live_pp = f"{stats.get('pp', 0):.2f}"
               
                bonus =  float(live_pp) - float(live_raw_pp)
                if bonus < 0: bonus = 0

                stars = []
                maps_ids = []
                for score in best_scores:
                    map_id = score['beatmap_id']
                    maps_ids.append(map_id)

                results, failed = await fetch_txt_beatmaps(maps_ids)

                if failed:
                    print("err loading maps (average_stats):", failed)

                for i, score in enumerate(best_scores):
                    acc = (score.get("accuracy", 1.0) * 100)
                    combo = score.get("combo", 0.0)
                    pp = score.get("pp", 0.0)
                    mods_str = score.get("mods", "")     
                    path = results.get(score['beatmap_id'], None)
                    score_stats = score.get("score_stats")
                    lazer = score.get("lazer")   

                    misses = score.get("misses", 0)
                    if miss_limit is not None and misses > miss_limit:
                        new_pp = pp
                        max_combo = combo
                        stars = score.get("stars", 0.0)  
                    else:
                        #neko API 
                        payload = {
                            "map_path": str(score.get('beatmap_id', "0")), 
                            
                            "n300": int(score_stats.get("count_300", 0)),
                            "n100": int(score_stats.get("count_100", 0)),
                            "n50": int(score_stats.get("count_50", 0)),
                            "misses": int(misses),                   
                            
                            "mods": str(score.get("mods", 0)), 
                            "combo": int(score.get("combo", 0.0)),      
                            "accuracy": float(score.get("accuracy", 1.0) * 100),    
                            
                            "lazer": bool(score.get('lazer', False)),          
                            "clock_rate": float(score.get('speed_multiplier') or 1.0),  

                            "custom_ar": float(score.get('AR', 0.0)),
                            "custom_cs": float(score.get('CS', 0.0)),
                            "custom_hp": float(score.get('HP', 0.0)),
                            "custom_od": float(score.get('OD', 0.0)),
                        }

                        try:
                            pp_data = await localapi.get_score_pp_neko_api(payload)

                            _pp = pp_data.get("pp")
                            max_pp = pp_data.get("no_choke_pp")
                            perfect_pp = pp_data.get("perfect_pp")

                            stars = pp_data.get("star_rating")
                            max_combo = pp_data.get("perfect_combo")
                            expected_bpm = pp_data.get("expected_bpm")

                        except Exception as e:
                            print(f"neko API failed: {e}")                     
                                                

                    score["index"] = i + 1
                    score["pp_old"] = pp
                    score["pp_new"] = max_pp
                    score["stars"] = stars
                    score["combo_old"] = combo
                    score["combo_max"] = max_combo

                    
                  
                best_scores = sorted(
                    best_scores, 
                    key=lambda s: s.get("pp_new", 0), 
                    reverse=True
                )
                for i, score in enumerate(best_scores):
                    score["weight_percent"] = 0.95 ** i
                
                total_pp = 0
                for i, score in enumerate(best_scores):
                    weight = 0.95 ** i
                    total_pp += score.get("pp_new", 0) * weight
                new_total = total_pp + bonus

                best_scores = [s for s in best_scores if s.get("misses", 0) != 0]

                if isinstance(best_scores, list) and best_scores:
                    if miss_limit is not None:
                        best_scores = [s for s in best_scores if s.get("misses", 0) <= miss_limit]
                    page_size = 5
                    total_pages = (len(best_scores) + page_size - 1) // page_size

                context.user_data["best_scores"] = best_scores
                context.user_data["user_data"] = user_data
                context.user_data["total_pages"] = total_pages

                if "user_data" not in context.user_data:
                    context.user_data["user_data"] = {}

                context.user_data["user_data"]["live_pp"] = live_pp
                context.user_data["user_data"]["new_total"] = new_total

                page_size = 10
                total_pages = (len(best_scores) + page_size - 1) // page_size
                page = 0

                text = get_page_text_choke(user_data, best_scores, page)
                keyboard = get_pagination_keyboard_choke(page, total_pages, update.effective_user.id)

    
                
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                        reply_markup=keyboard
                    )
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                        reply_markup=keyboard
                    )


                return
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных по топ-100.")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при nochoke (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Непонятно... Попробуй еще раз через несколько секунд!`\n\n"
                        "✨*/help*"
                        " | `/help nochoke`\n\n",
                    parse_mode="Markdown"
                )
def get_page_text_choke(user_data, best_scores, page=0, page_size=5):
    start = page * page_size
    end = start + page_size
    lines = []
    a, b = float(user_data["live_pp"]), float(user_data["new_total"])
    lines.append(f'<b>Total pp: {a:.2f} → {b:.2f}pp (+{(b-a):.2f})</b>')
    lines.append("")       
    for i, score in enumerate(best_scores[start:end], start=start):
        # score["weight_percent"] = 0.95 ** i

        title = html.escape(score.get("title", ""))
        version = html.escape(score.get("version", ""))
        mods = score.get("mods", [])
        mods_str = "NM" if not mods else "".join(mods)
        if score.get('lazer') == False:
            mods_str += 'CL'
        mods_str = html.escape(mods_str)        
        stars = score.get("stars", 0)
        pp_old = f"{score.get('pp_old',0):.2f}"
        pp_new = f"{score.get('pp_new',0):.2f}"
        misses = str(score.get("misses", 0))
        map_id = score.get("beatmap_id")

        url = f"https://osu.ppy.sh/beatmaps/{map_id}"
        url_2 = f"https://myangelfujiya.ru/darkness/direct?id={map_id}"

        line1 = f'<b>#{score.get("index")}</b> <a href="{url}">{title} [{version}]</a> <b>+{mods_str}</b> [{stars:.2f}★]'
        line2 = f'<a href="{url_2}">🔗</a> <code>{pp_old}</code> → <b>{pp_new}pp</b> • <i>Removed {misses}❌</i>'

        lines.append(line1)
        lines.append(line2)
        lines.append("")

    username = html.escape(user_data["username"])
    stats = user_data["statistics"]
    pp_text = f"{stats.get('pp', 0):.2f}"
    global_rank_text = f"(#{stats.get('global_rank'):,})" if stats.get("global_rank") else "(#????)"
    country_rank_text = f"{user_data['country_code']}#{stats.get('country_rank'):,}" if stats.get("country_rank") else f"{user_data['country_code']}#??"
    rank_text = f"{username}: {pp_text}pp {global_rank_text} {country_rank_text}"
    country_flag = country_code_to_flag(user_data["country_code"])
    user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
    user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'

    text = f"{user_link}\n\n" + "\n".join(lines)
    return text


async def page_callback_choke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 

    best_scores = context.user_data.get("best_scores", [])
    user_data = context.user_data.get("user_data")
    total_pages = context.user_data.get("total_pages", 1)

    _, page_str, owner_id_str = query.data.split("_")
    owner_id = int(owner_id_str)
    if query.from_user.id != owner_id:
        await query.answer("Это не ваша команда!", show_alert=True)
        return

    page = int(page_str)
    text = get_page_text_choke(user_data, best_scores, page)  # твоя функция генерации текста
    keyboard = get_pagination_keyboard_choke(page, total_pages, owner_id)

    await query.edit_message_text(
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )

async def show_scores_choke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    best_scores = context.user_data.get("best_scores", [])
    user_data = context.user_data.get("user_data")
    total_pages = context.user_data.get("total_pages", 1)

    user_id = update.effective_user.id
    page = 0
    text = get_page_text_choke(user_data, best_scores, page)
    keyboard = get_pagination_keyboard_choke(page, total_pages, user_id)

    await update.message.reply_text(
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=keyboard
    )

# avg stats cmd
async def start_average_stats(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(average_stats(update, context, user_request))
async def average_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    can_run = await check_user_cooldown(
            command_name="average_stats",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_STATS_COMMANDS,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_STATS_COMMANDS} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3 

    user_id = str(update.message.from_user.id)
    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if not context.args:
        if saved_name:
            username = saved_name
        else:
            text = (
                "Использование: `/average_stats fujina123` <- никнейм\n\n\n"
                "⚙ *Дополнительно*\n\n"
                "/name – сохранить ник\n"
            )
            await safe_send_message(update, text, parse_mode="Markdown")
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'

    temp_message = await update.message.reply_text(
        "`Загрузка...`", 
        parse_mode="Markdown"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            token = await get_osu_token()
            user_data = await asyncio.wait_for(get_user_profile(username, token=token), timeout=10)
            if not user_data:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Игрок не найден`",
                    parse_mode="Markdown"
                )
                return

            try:
                user_id = user_data["id"]
                best_scores = await asyncio.wait_for(get_top_100_scores(username, token, user_id), timeout=10)
            except Exception as e:
                best_scores = "N/A"
                print(e)
            

            if isinstance(best_scores, list) and best_scores:
                def format_value(val, is_time=False):
                    if is_time:
                        minutes = int(val // 60)
                        seconds = int(val % 60)
                        return f"{minutes}:{seconds:02d}"
                    if isinstance(val, float):
                        return f"{val:.2f}"
                    return str(val)

                accs, combos, misses, pps = [], [], [], []
                stars, ars, css, hps, ods, bpms, lengths = [], [], [], [], [], [], []

                # beatmap_requests = []
                # for score in best_scores:
                #     beatmap_requests.append({
                #         "beatmap_id": score.get("beatmap_id"),
                #         "mods": score.get("mods", []),  # список модов
                #         "ruleset_id": 0  # стандартный osu! ruleset
                #     })

                # attributes_list = await get_beatmap_attributes_batch(beatmap_requests, token=token, parallel_limit=5, delay_between_batches=0.1)

                maps_ids = []
                for score in best_scores:
                    map_id = score['beatmap_id']
                    maps_ids.append(map_id)

                results, failed = await fetch_txt_beatmaps(maps_ids)

                if failed:
                    print("err loading maps (average_stats):", failed)

                for i, score in enumerate(best_scores):
                    accs.append(score.get("accuracy", 0.0) * 100)  # accuracy в %
                    combos.append(score.get("combo", 0))
                    misses.append(score.get("misses", 0))
                    pps.append(score.get("pp", 0.0))
                    # stars = (score.get("stars", 0.0))
                    ar = (score.get("AR", 0.0))
                    cs = (score.get("CS", 0.0))
                    hp = (score.get("HP", 0.0))
                    od = (score.get("OD", 0.0))
                    bpm = (score.get("bpm", 0.0))
                    length = (score.get("length", 0))
                    
                    mods_str = score.get("mods", "")
                    speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)
                   
                    #neko API 
                    payload = {
                        "map_path": str(score.get('beatmap_id', "0")), 
                        
                        "n300": 0,
                        "n100": 0,
                        "n50": 0,
                        "misses": 0,                   
                        
                        "mods": str(mods_str), 
                        "combo": int(0),      
                        "accuracy": float(0.0),    
                        
                        "lazer": bool(True),          
                        "clock_rate": float(1.0),  

                        "custom_ar": float(ar),
                        "custom_cs": float(cs),
                        "custom_hp": float(hp),
                        "custom_od": float(od),
                    }

                    try:
                        pp_data = await localapi.get_map_stats_neko_api(payload)

                        # pp = pp_data.get("pp")
                        # choke = pp_data.get("no_choke_pp")
                        # max_pp = pp_data.get("perfect_pp")

                        map_stars = pp_data.get("star_rating")
                        # max_combo = pp_data.get("perfect_combo")
                        # expected_bpm = pp_data.get("expected_bpm")

                        # n300 = pp_data.get("n300")
                        # n100 = pp_data.get("n100") 
                        # n50 = pp_data.get("n50")
                        # expected_miss = pp_data.get("misses")

                        # aim_raw = pp_data.get("aim")
                        # acc_raw = pp_data.get("acc")
                        # speed_raw = pp_data.get("speed")                        
                        
                        if map_stars > 8.0: 
                            print(score['beatmap_id'])
                    except Exception as e:
                        print(f"neko API failed: {e}")

                    stars.append(map_stars)

                    bpm, ar, od, cs, hp = apply_mods_to_stats(
                        bpm, ar, od, cs, hp,
                        speed_multiplier=speed_multiplier, hr=hr_active, ez=ez_active
                    )
                    length = int(round(float(length) / speed_multiplier))

                    ars.append(ar)
                    css.append(cs)
                    hps.append(hp)
                    ods.append(od)
                    bpms.append(bpm)
                    lengths.append(length)

                                    
                def calc_stats(values):
                    numeric_values = [v for v in values if isinstance(v, (int, float))]
                    if not numeric_values:
                        return ("-", "-", "-")
                    return (min(numeric_values), mean(numeric_values), max(numeric_values))

                def format_time(seconds):
                    if isinstance(seconds, str):
                        return seconds
                    m, s = divmod(int(round(seconds)), 60)
                    h, m = divmod(m, 60)
                    if h > 0:
                        return f"{h}:{m:02d}:{s:02d}"
                    return f"{m}:{s:02d}"

                table_data = {
                    "Accuracy": calc_stats(accs),
                    "Combo": calc_stats(combos),
                    "Misses": calc_stats(misses),
                    "Stars": calc_stats(stars),
                    "PP": calc_stats(pps),
                    "AR": calc_stats(ars),
                    "CS": calc_stats(css),
                    "HP": calc_stats(hps),
                    "OD": calc_stats(ods),
                    "BPM": calc_stats(bpms),
                    "Length": calc_stats(lengths),
                }

                formatted_table_data = {}
                for key, values in table_data.items():
                    formatted_values = []
                    for v in values:
                        if isinstance(v, str):
                            formatted_values.append(v)
                        elif key == "Length":
                            formatted_values.append(format_time(v))
                        elif isinstance(v, float):
                            formatted_values.append(f"{v:.2f}")
                        else:
                            formatted_values.append(str(v))
                    formatted_table_data[key] = formatted_values

                headers = ["", "Minimum", "Average", "Maximum"]
                rows = [[key, *values] for key, values in formatted_table_data.items()]

                col_widths = [
                    max(len(str(headers[i])), max(len(str(row[i])) for row in rows))
                    for i in range(len(headers))
                ]

                def fmt_row(row):
                    return " | ".join(
                        str(row[i]).ljust(col_widths[i]) if i == 0 else str(row[i]).center(col_widths[i])
                        for i in range(len(row))
                    )

                header_line = fmt_row(headers)
                sep_line = "-+-".join("-" * w for w in col_widths)
                table_lines = [header_line, sep_line] + [fmt_row(row) for row in rows]

                table_str = "\n".join(table_lines)

                username = user_data["username"]
                stats = user_data["statistics"]

                pp_text = f"{stats.get('pp')}" if stats.get("pp") else "0"
                global_rank_text = f"(#{stats.get('global_rank'):,}" if stats.get("global_rank") else "(#????"
                country_rank_text = (
                    f"  {user_data['country_code']}#{stats.get('country_rank'):,})"
                    if stats.get("country_rank") else f"  {user_data['country_code']}#???)"
                )

                rank_text = f"{username}: {pp_text}pp {global_rank_text}{country_rank_text}"
                country_flag = country_code_to_flag(user_data["country_code"])

                user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
                user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'

                text = f"{user_link}\n\n<pre>{table_str}</pre>"


                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=temp_message.message_id,
                        text=text,
                        parse_mode="HTML"
                    )
                    return
                except:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="HTML"            
                )
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Нет данных по топ-100.")

            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=temp_message.message_id)
            return

        except Exception as e:
            print(f"Ошибка при average_stats (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )

#music cmd
async def start_beatmap_audio(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(beatmap_audio(update, context, user_request))
async def beatmap_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request=True):
    url = update.message.text.strip()
    match = re.search(r"beatmapsets/(\d+)", url)

    if user_request:
        if not match:        
            msg = await update.message.reply_text(
                "❌ Нужна ссылка на карту"
            )
            asyncio.create_task(delete_message_after_delay(context, msg.chat.id, msg.message_id, 5))
            asyncio.create_task(delete_user_message(update, context, delay=4))
            return
    
    try:
        if match is None: return
        beatmap_id = match.group(1)
    except Exception as e:
        print(e)
        return

    if user_request: warn_text = f"⏳ Подождите {COOLDOWN_MP3_COMMAND} секунд"
    else: warn_text = None
    can_run = await check_user_cooldown(
        command_name="render_score",
        user_id=str(update.effective_user.id),
        cooldown_seconds=COOLDOWN_MP3_COMMAND,           
        update=update,
        context=context,
        warn_text=warn_text
    )
    if not can_run:
        return

    max_attempts = 3
    if user_request:
        for _ in range(max_attempts):
            try:
                status_msg = await update.message.reply_text("Загрузка...")
                break
            except Exception as e: print(e)
    
    for _ in range(max_attempts):
        try: 
            await download_osz_async(beatmap_id, OSU_SESSION, OSZ_DIR)

            break
        except Exception as e: print(e)   

    path = os.path.join(OSZ_DIR, beatmap_id)

    title, artist, path, bg_path = await beatmap_artists_and_audio_path(path)

    path = os.path.join(OSZ_DIR, beatmap_id, path)
    bg_path = os.path.join(OSZ_DIR, beatmap_id, bg_path)

    await send_audio(update, context, path, title, artist, bg_path)
    if user_request:
        asyncio.create_task(delete_message_after_delay(context, status_msg.chat_id, status_msg.message_id, 1)) 
async def send_audio(update: Update, context: ContextTypes.DEFAULT_TYPE, audio_file_path, title=None, artist=None, bg=None):
    path = Path(audio_file_path)
    if not path.is_file():
        print("Файл не найден:", audio_file_path)
        return
    if os.path.getsize(audio_file_path) == 0:
        print("Файл пустой:", audio_file_path)
        return

    temp_file = None
    try:
        if path.suffix.lower() == ".ogg":
            # создаём временный файл с расширением .mp3
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_file.close()  # закрываем, чтобы pydub смог писать
            audio = AudioSegment.from_file(audio_file_path, format="ogg")
            audio.export(temp_file.name, format="mp3")
            send_path = Path(temp_file.name)
        else:
            send_path = path

        username = escape_markdown(update.effective_user.username, version=2)
        link = "https://t.me/fujiyaosubot"
        caption = f"@{username} 💃 [ᴅᴀʀᴋɴᴇss]({link})"

        with open(send_path, "rb") as f:
            kwargs = {
                "audio": InputFile(f, filename=send_path.name),
                "caption": caption,
                "title": title or "",
                "parse_mode": "MarkdownV2",
            }
            if artist:
                kwargs["performer"] = artist

            await update.message.reply_audio(**kwargs)

    except Exception as e:
        print("Ошибка при отправке аудио:", e)
    finally:
        # удаляем временный файл, если он был
        if temp_file:
            try:
                os.remove(temp_file.name)
            except OSError:
                pass
async def beatmap_artists_and_audio_path(folder_path: str) -> tuple[Optional[str], Optional[str]]:
    """
    Ищет первый .osu в папке и возвращает:
    (строка "Title - Artist" (Unicode если есть), имя аудиофайла)
    """
    osu_files = [f for f in os.listdir(folder_path) if f.endswith(".osu")]
    if not osu_files:
        print(f"⚠ В папке {folder_path} нет .osu файлов")
        return None, None

    path_to_map = os.path.join(folder_path, osu_files[0])

    title = None
    artist = None
    title_unicode = None
    artist_unicode = None
    audio_filename = None
    bg_path = None

    try:
        with open(path_to_map, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("TitleUnicode:"):
                    title_unicode = line.split(":", 1)[1].strip()
                elif line.startswith("ArtistUnicode:"):
                    artist_unicode = line.split(":", 1)[1].strip()
                elif line.startswith("Title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("Artist:"):
                    artist = line.split(":", 1)[1].strip()
                elif line.startswith("AudioFilename:"):
                    audio_filename = line.split(":", 1)[1].strip()
                elif '"' in line and any(ext in line.lower() for ext in [".jpg", ".jpeg", ".png"]):
                    m = re.search(r'"([^"]+\.(?:jpg|jpeg|png))"', line, re.IGNORECASE)
                    if m:
                        bg_path = m.group(1)
                if (title_unicode or title) and (artist_unicode or artist) and audio_filename and bg_path:
                    break
    except Exception as e:
        print(f"⚠ Ошибка при парсинге {path_to_map}: {e}")
        return None, None, None, None

    final_title = title_unicode if title_unicode else title
    final_artist = artist_unicode if artist_unicode else artist

    return final_title, final_artist, audio_filename, bg_path


def search_beatmaps(db_path, mods=None, filters=None, limit=10, offset=0, order_by_total=True, lazer=True):
                """
                db_path: путь к beatmaps.db
                mods: список модов, например ["DTHD", "HR"]
                filters: словарь с ключами 'aim', 'speed', 'acc', значениями кортежа (operator, value) или (min, max)
                        Пример: {"aim": (100, 200), "speed": (90, 140), "acc": (">", 90)}
                limit: количество результатов
                offset: смещение
                order_by_total: сортировать по сумме aim+speed+acc
                """

                conn = sqlite3.connect(db_path)
                cur = conn.cursor()

                where_clauses = []
                params = []

                if mods:
                    placeholders = ",".join("?" for _ in mods)
                    where_clauses.append(f"mod IN ({placeholders})")
                    params.extend(mods)

                if filters:
                    for stat, val in filters.items():
                        if isinstance(val, tuple) and len(val) == 2 and all(isinstance(v, (int, float)) for v in val):
                            
                            where_clauses.append(f"{stat} BETWEEN ? AND ?")
                            params.extend(val)
                        elif isinstance(val, tuple) and len(val) == 2 and isinstance(val[0], str):
                            
                            op, v = val
                            where_clauses.append(f"{stat} {op} ?")
                            params.append(v)

                where_clauses.append("mode = ?")
                params.append("lazer" if lazer else "stable")

                where_sql = " AND ".join(where_clauses)
            
                sql = f"""
                    SELECT map_id, mode, mod, aim, speed, acc, (aim + speed + acc) AS total
                    FROM beatmaps
                    {f'WHERE {where_sql}' if where_sql else ''}
                    {'ORDER BY total DESC' if order_by_total else ''}
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])

                cur.execute(sql, params)
                results = cur.fetchall()
                conn.close()
                return results
async def start_farm(update, context, user_request=True):
    await log_all_update(update)
    asyncio.create_task(farm(update, context, user_request))
async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE, user_request):
    query = update.callback_query
    if query:  
        await query.answer()
        message = query.message
    else:
        message = update.message

    can_run = await check_user_cooldown(
            command_name="farm",
            user_id=str(update.effective_user.id),
            cooldown_seconds=COOLDOWN_FARM_COMMAND,           
            update=update,
            context=context,
            warn_text=f"⏳ Подождите {COOLDOWN_FARM_COMMAND} секунд"
        )
    if not can_run:
        return
    MAX_ATTEMPTS = 3

    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if update.message:
        temp_message = await update.message.reply_text(
            "`Загрузка...`",
            parse_mode="Markdown"
        )

    if not context.args:
        if saved_name:
            username = saved_name
        else:       
            await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text="`Для использования этой команды должно быть сохранено имя /name`" ,
                    parse_mode="Markdown"
                )
            return
    else:
        username = " ".join(context.args)

    if saved_name is None:
        saved_name = 'нет'
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:  
            try: 
                if os.path.exists(USERS_SKILLS_FILE):
                    with open(USERS_SKILLS_FILE, "r", encoding="utf-8") as f:
                        users_skills = json.load(f)
                else:    
                    users_skills = {}
                
                if username in users_skills:
                    skills = users_skills[username].get("values", {})
                else:
                    raise ValueError(f"Пользователь {username} не найден в JSON")        
            except Exception as e:
                print(e)
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`Нет данных о карточке пользователя... Может быть стоит создать новую командой /card, а после этого вернуться сюда?`",
                    parse_mode="Markdown"
                )
                return

            context.user_data["farm_user_id"] = update.effective_user.id
            context.user_data["farm_choices"] = {}
            context.user_data["farm_step"] = 0
            context.user_data["farm_topic_id"] = getattr(update.effective_message, "message_thread_id", None)

           
            await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"Версия:",
                    parse_mode="Markdown",
                    reply_markup=get_farm_step_keyboard(0)
            )

            return
        except Exception as e:
            print(f"Ошибка при farm (попытка {attempt}/{MAX_ATTEMPTS}): {e}")
            if attempt == MAX_ATTEMPTS:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=temp_message.message_id,
                    text=f"`ошибка после {MAX_ATTEMPTS} попыток...`",
                    parse_mode="Markdown"
                )


async def farm_pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split(":")
    action, user_id, page = data
    user_id = int(user_id)
    page = int(page)

    if query.from_user.id != user_id:
        await query.answer("❌ Это не ваша команда", show_alert=True)
        return

    pages = context.user_data.get("farm_pages", [])
    if not pages:
        await query.edit_message_text("❌ Ошибка: данные не найдены")
        return

    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if os.path.exists(USERS_SKILLS_FILE):
        with open(USERS_SKILLS_FILE, "r", encoding="utf-8") as f:
            users_skills = json.load(f)
    else:    
        users_skills = {}
    
    if saved_name in users_skills:
        skills = users_skills[saved_name].get("values", {})
    else:
        raise ValueError(f"Пользователь {saved_name} не найден в JSON")

    aim_base = skills.get("aim_total", 0)
    speed_base = skills.get("speed_total", 0)
    acc_base = skills.get("acc_total", 0)

    lines = []
    choices = context.user_data.get("farm_choices", {})
    skill_level = choices.get("skill", "1")
    percent = (float(choices.get("tol", 1.2)) - 1) * 100
    percent_str = f"{percent:.0f}%"
    lvl = (int(skill_level) -1) * 10 + 30
    lvl_str = f"Lvl {lvl}"
    line = f"1️⃣ Acc. 2️⃣ Aim 3️⃣ Speed 🔎{lvl_str}|±{percent_str}\n"
    lines.append(line)
    for beatmap in pages[page]:
        map_id = beatmap[0]
        mods = beatmap[2]
        aim, speed, acc = beatmap[3], beatmap[4], beatmap[5]

        total = aim + speed + acc
        total_str = f"{total:.0f}"

        def cmp_symbol(val, base):
            if val > base + 15:
                return "🔼"
            elif val < base - 15:
                return "🔽"
            else:
                return "🔅"

        symbols = "".join([            
            cmp_symbol(acc, acc_base),
            cmp_symbol(aim, aim_base),
            cmp_symbol(speed, speed_base),
        ])

        url = f"https://osu.ppy.sh/beatmaps/{map_id}"
        url_2 = f"https://myangelfujiya.ru/darkness/direct?id={map_id}"

        line = f"{total_str}pts {symbols} [http://osu.p...]({url}) | [🔗]({url_2})   +{mods}"
        lines.append(line)

    text = "\n".join(lines)

    keyboard = create_pagination_keyboard(page, len(pages), user_id)  # <-- тоже page

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )


async def farm_step_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != context.user_data.get("farm_user_id"):
        await query.answer("❌ Это не ваша команда", show_alert=True)
        return

    data = query.data.split(":")  # farm_skill:medium
    param_type, value = data

    if param_type == "farm_skill":
        context.user_data["farm_choices"]["skill"] = value
    elif param_type == "farm_mod":
        context.user_data["farm_choices"]["mod"] = value
    elif param_type == "farm_lazer":
        context.user_data["farm_choices"]["lazer"] = value == "True"
    elif param_type == "farm_tol":
        context.user_data["farm_choices"]["tol"] = value

    context.user_data["farm_step"] += 1
    step = context.user_data["farm_step"]

    if step > 3:
        await query.edit_message_text(f"⏳ @{query.from_user.username}...")
        await generate_farm_results(update, context)
    else:
        if step == 0: text="Клиент?"
        elif step == 1:text="Интенсивность фарма? (80-90% около топскора)"
        elif step == 2:text="Разброс, меньше - точнее уровень прошлого меню, а больше - больше карт за счет увеличения диапазона поиска"
        else:text="Моды, с которыми будет карта"
        await query.edit_message_text(
            text,
            reply_markup=get_farm_step_keyboard(step)
        )
async def generate_farm_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("farm_user_id")
    choices = context.user_data.get("farm_choices", {})
    topic_id = context.user_data.get("farm_topic_id", None)

    if not choices:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text="❌ Ошибка: параметры поиска не выбраны"
        )
        return

    saved_name = await auth.check_osu_verified(str(update.effective_user.id))

    if os.path.exists(USERS_SKILLS_FILE):
        with open(USERS_SKILLS_FILE, "r", encoding="utf-8") as f:
            users_skills = json.load(f)
    else:    
        users_skills = {}
    
    if saved_name in users_skills:
        skills = users_skills[saved_name].get("values", {})
        aim = skills.get("aim_total", 0)
        speed = skills.get("speed_total", 0)
        acc = skills.get("acc_total", 0)
        print(f"    Навыки пользователя {saved_name}: aim={aim}, speed={speed}, acc={acc}")
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text="❌ Навыки пользователя не найдены. Создайте карточку через /card."
        )
        raise ValueError(f"Пользователь {saved_name} не найден в JSON")


    skill_level = choices.get("skill", "low")
    mod = choices.get("mod", "NM")
    lazer = choices.get("lazer", "True")
    tol = float(choices.get("tol", 1.2))

    if skill_level == "1":
        base_start, base_end = 0.35, 0.45
    elif skill_level == "2":
        base_start, base_end = 0.45, 0.55
    elif skill_level == "3":
        base_start, base_end = 0.55, 0.65
    elif skill_level == "4":
        base_start, base_end = 0.65, 0.75
    elif skill_level == "5":
        base_start, base_end = 0.75, 0.85
    elif skill_level == "6":
        base_start, base_end = 0.85, 0.95
    elif skill_level == "7":
        base_start, base_end = 0.95, 1.05
    elif skill_level == "8":
        base_start, base_end = 1.05, 1.15
    elif skill_level == "9":
        base_start, base_end = 1.15, 1.25
    else:  # high
        base_start, base_end = 1.25, 1.35

    static_mult = 1.0
    start_mult = base_start / (tol*static_mult)
    end_mult = base_end * (tol*static_mult)

    #if skill_level == "floor":
    #    base_start, base_end = 0.4, 0.6
    #elif skill_level == "low":
    #    base_start, base_end = 0.6, 0.8
    #elif skill_level == "medium":
    #    base_start, base_end = 0.8, 1.0
    #else:  # high
    #    base_start, base_end = 1.0, 1.3

    #start_mult = base_start / tol 
    #end_mult = base_end * tol      

    filters = {
        "aim": (aim * start_mult, aim * end_mult),
        "speed": (speed * start_mult, speed * end_mult),
        "acc": (acc * start_mult, acc * end_mult)
    }

    mods = [mod]
    limit = 800
    offset = 0   

    try:
        results = search_beatmaps(
            db_path=f"{BOT_DIR}/beatmaps.db",
            mods=mods,
            filters=filters,
            limit=limit,
            offset=offset,
            lazer=lazer
        )

    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text=f"❌ Ошибка при поиске карт: {e}"
        )
        return

    if not results:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=topic_id,
            text="🚮 Ничего не найдено, попробуй увеличить разброс или другой уровень скилов."
        )
        return

    PAGE_SIZE = 8
    pages = [results[i:i+PAGE_SIZE] for i in range(0, len(results), PAGE_SIZE)]
    context.user_data["farm_pages"] = pages

    aim_base = skills.get("aim_total", 0)
    speed_base = skills.get("speed_total", 0)
    acc_base = skills.get("acc_total", 0)

    # --- Отправляем первую страницу ---
    current_page = 0
    lines = []
    percent = (tol - 1) * 100
    percent_str = f"{percent:.0f}%"
    lvl = (int(skill_level) -1) * 10 + 30
    lvl_str = f"Lvl {lvl}"
    line = f"1️⃣ Acc. 2️⃣ Aim 3️⃣ Speed 🔎{lvl_str}|±{percent_str}\n"
    lines.append(line)
    for beatmap in pages[current_page]:
        map_id = beatmap[0]
        lazer = beatmap[1].upper()
        mods = beatmap[2]
        aim, speed, acc = beatmap[3], beatmap[4], beatmap[5]

        total = aim + speed + acc
        total_str = f"{total:.0f}"

        # сравниваем с базовыми
        def cmp_symbol(val, base):
            if val > base + 15:
                return "🔼"
            elif val < base - 15:
                return "🔽"
            else:
                return "🔅"

        symbols = "".join([            
            cmp_symbol(acc, acc_base),
            cmp_symbol(aim, aim_base),
            cmp_symbol(speed, speed_base),
        ])

        url = f"https://osu.ppy.sh/beatmaps/{map_id}"
        url_2 = f"https://myangelfujiya.ru/darkness/direct?id={map_id}"

        line = f"{total_str}pts {symbols} [http://osu.p...]({url}) | [🔗]({url_2})   +{mods}"
        lines.append(line)
    line = """\n            🔼 — скилл карты больше твоего
            🔽 — твой скилл больше, карта легче
            🔅 — такой же скилл, как твой"""
    lines.append(line)
    text = "\n".join(lines)

    keyboard = create_pagination_keyboard(current_page, len(pages), user_id)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=topic_id,
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown",
        disable_web_page_preview=True

    )

#logs&startup
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO  
)
logger = logging.getLogger(__name__)
def cleanup_temp():
    for f in glob.glob(os.path.join(TEMP_DIR, "*.png")):
        try:
            os.remove(f)
        except:
            pass
atexit.register(cleanup_temp)
def cleanup_flags():
    flags_dir = os.path.join(BOT_DIR, "stats", "flags")
    
    if os.path.exists(flags_dir):
        for f in os.listdir(flags_dir):
            try:
                os.remove(os.path.join(flags_dir, f))
            except Exception:
                pass
    else:
        os.makedirs(flags_dir, exist_ok=True)      
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, check_message))
    
    #async
    app.add_handler(CommandHandler("mods", start_mods))
    app.add_handler(CommandHandler("mappers", start_mappers))

    app.add_handler(CommandHandler("profile", start_profile))
    app.add_handler(CommandHandler("p", start_profile))

    app.add_handler(CommandHandler("card", start_card))  
    app.add_handler(CommandHandler("c", start_card))  

    app.add_handler(CommandHandler("recent_fix", start_recent_fix))
    app.add_handler(CommandHandler("fix", start_recent_fix))
    app.add_handler(CommandHandler("f", start_recent_fix))   
    
    app.add_handler(CommandHandler("recent", start_rs))
    app.add_handler(CommandHandler("rs", start_rs))    
    app.add_handler(CommandHandler("r", start_rs))

    app.add_handler(CommandHandler("pc", start_compare_profile))    
 
    app.add_handler(CommandHandler("start", start_help))
    app.add_handler(CommandHandler("help", start_help))
      
    app.add_handler(CommandHandler("music", start_beatmap_audio))

    app.add_handler(CommandHandler("maps_skill", start_farm))
    app.add_handler(CommandHandler("ms", start_farm))
    
    app.add_handler(CommandHandler("average", start_average_stats))
    app.add_handler(CommandHandler("avg", start_average_stats))
    app.add_handler(CommandHandler("a", start_average_stats))

    app.add_handler(CommandHandler("nochoke", start_nochoke))
    app.add_handler(CommandHandler("n", start_nochoke))

    #TODO make async
    app.add_handler(CommandHandler("simulate", simulate))
    app.add_handler(CommandHandler("s", simulate))

    app.add_handler(CommandHandler("settings", settings_command_handler))  

    app.add_handler(CommandHandler("beatmaps", beatmaps))
    app.add_handler(CommandHandler("b", beatmaps))

    app.add_handler(CommandHandler("name", set_name))
    app.add_handler(CommandHandler("link", set_name))
    app.add_handler(CommandHandler("nick", set_name))
    app.add_handler(CommandHandler("osu", set_name))

    app.add_handler(CommandHandler("gn", random_image))    

    app.add_handler(CommandHandler("doubt", doubt))
    app.add_handler(CommandHandler("blacks", blacks))

    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("uptime", uptime))
    app.add_handler(CommandHandler("getthreads", dev_getthreads))

    app.add_handler(CommandHandler("challenge", challenge))


    app.add_handler(CallbackQueryHandler(rs_button, pattern=r"^rs_"))
    app.add_handler(CallbackQueryHandler(button_handler_profile, pattern=r"^(profile|card|noop)$"))
    app.add_handler(CallbackQueryHandler(beatmaps_button_handler, pattern="^beatmaps_"))    
    app.add_handler(CallbackQueryHandler(settings_button_handler, pattern="^settings_"))
    # app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^(next_challenge|finish_challenge|leaderboard|info|skip_challenge|menu_challenge)$"))
    app.add_handler(CallbackQueryHandler(simulate_button_handler, pattern="^simulate_"))

    app.add_handler(CallbackQueryHandler(farm_pagination_callback, pattern=r"^farm_page:"))
    app.add_handler(CallbackQueryHandler(farm_step_callback, pattern=r"^farm_(skill|mod|lazer|tol):"))
    app.add_handler(CallbackQueryHandler(page_callback_choke, pattern=r"^page_\d+_\d+$"))
    
    app.add_handler(CommandHandler("reminders", reminders_command))

    class ShortNetworkHandler(logging.Handler):
        def emit(self, record):
            msg = record.getMessage()
            if "NetworkError" in msg: print("NetworkError")
            else: print(msg)
    logger.addHandler(ShortNetworkHandler())
    cleanup_flags()

    try: app.run_polling()
    except NetworkError:  print("NetworkError")
if __name__ == "__main__":
    main()