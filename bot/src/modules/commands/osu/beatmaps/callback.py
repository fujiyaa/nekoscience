


import os
import asyncio
import time
import temp
import json
import html
from collections import Counter

from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from ....actions.messages import safe_query_answer, delete_message_after_delay
from ....systems.auth import check_osu_verified
from ....external.osu_api import get_osu_token, get_most_played, get_top_100_scores
from ....utils.text_format import build_beatmaps_text
from .processing import worker, check_group_status, delete_done_file, addtask
from .buttons import get_keyboard

from config import COOLDOWN_WEEK_SECONDS, FLAG_FILE, COUNT_ME_FILE, GROUPS_DIR



async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        msg, reply_markup = await build_beatmaps_text(owner_id), get_keyboard(owner_id)
        
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
        
        saved_name = await check_osu_verified(str(update.effective_user.id))
                
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

            saved_name = await check_osu_verified(str(update.effective_user.id))
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
