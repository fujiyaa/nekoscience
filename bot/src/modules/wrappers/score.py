


import io 
import html
import temp
import traceback
from datetime import datetime
from telegram import Update, InputMediaPhoto, LinkPreviewOptions

from ..utils import text_format
from ..external.osu_http import beatmap
from ..utils.osu_conversions import get_mods_info, apply_mods_to_stats
from ..wrappers.beatmap import create_beatmap_image
# from ..wrappers.score_image_v2 import get_score_caption
from ..utils.calculate import caclulte_cached_entry
from ..actions.rich import rich_reply, edit_rich_message

from config import USER_SETTINGS_FILE



# универсальная для команд где нужен скор
async def process_score_and_image(cached_entry: dict, image_todo_flag: bool = False, is_recent: bool = True): 
    user =              cached_entry['user']
    map =               cached_entry['map']
    osu_api_data =      cached_entry['osu_api_data']
    osu_score =         cached_entry['osu_score']
    neko_api_calc =     cached_entry['neko_api_calc']
    lazer_data =        cached_entry['lazer_data']
    osu_statistics_max= cached_entry['osu_statistics_max']
    state =             cached_entry['state']
    meta =              cached_entry['meta']    

    if not cached_entry['state']['calculated']:
        await caclulte_cached_entry(cached_entry)
        
        neko_api_calc = cached_entry['neko_api_calc']
        state =         cached_entry['state']
        meta =          cached_entry['meta']        

    lazer = state.get('lazer')
    
    mods_str = osu_score.get("mods", "")
    mods_text = text_format.normalize_no_plus(mods_str)
    speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)

    map_id = map.get('beatmap_id')
    _path, base_values = await beatmap(int(map_id))

    # карты без ar
    base_values["ar"] = map.get("ar", 5) if base_values.get("ar") is None else base_values["ar"]
    
    if not isinstance(lazer_data.get("DA_values"), dict):
        lazer_data["DA_values"] = {}

    base_ar = lazer_data.get("DA_values", {}).get("approach_rate", base_values["ar"])
    base_cs = lazer_data.get("DA_values", {}).get("circle_size", base_values["cs"])
    base_od = lazer_data.get("DA_values", {}).get("overall_difficulty",base_values["od"])
    base_hp = lazer_data.get("DA_values", {}).get("drain_rate", base_values["hp"])

    map_cs = map.get("cs", {}) or 0
    map_ar = map.get("ar", {}) or 0
    map_od = map.get("od", {}) or 0
    map_hp = map.get("hp", {}) or 0
    
    pp = neko_api_calc.get("pp")
    max_pp = neko_api_calc.get("no_choke_pp")
    perfect_pp = neko_api_calc.get("perfect_pp")

    stars = neko_api_calc.get("star_rating")
    perfect_combo = neko_api_calc.get("perfect_combo")
    expected_bpm = neko_api_calc.get("expected_bpm")        
    
          
    #temp pp fix
    pp = pp if not isinstance(osu_score.get("pp"), (int, float)) or osu_score.get("pp") <= 0 else osu_score.get("pp")
    
    
    accuracy = osu_score.get('accuracy')

    if lazer:
        rank = lazer_data.get('rank') 
    else:        
        rank = osu_api_data.get('rank_legacy') 

    accuracy_display = round(accuracy * 100, 2)
    accuracy_display = (f"{accuracy_display}%")

    # if lazer:   
    #     if accuracy == 100:
    #         rank = 'SS'
    #     elif accuracy >= 90:
    #         if (osu_score.get('count_miss') == 0) and (accuracy >= 95):
    #             rank = 'S'
    #         else:
    #             rank = 'A'
    #     elif accuracy >= 80:
    #         rank = 'B'
    #     elif accuracy >= 70:
    #         rank = 'C'
    #     else:
    #         rank = 'D'
    
    username = user.get("username")
    pp_text = user.get('total_pp', '0')
    pp_profile_text_alt = pp_text
    # global_rank_text = f"(#{user.get('global_rank'):,}" if user.get("global_rank") else "(#????"
    global_rank_text_alt = f"#{user.get('global_rank'):,}" if user.get("global_rank") else "#????" 
    # rank_text = f"{username}: {pp_text}pp {global_rank_text})"    
    country_flag = text_format.country_code_to_flag(country_code = user.get("country_code")) 

    beatmap_escaped = html.escape(map.get('beatmap_full'))
    
    try_count, failed = osu_score.get('try_count'), osu_score.get('failed')
    try_text = ''
    if try_count > 1:
        try_text = f"<i><b>- Try #{try_count}</b></i>"

    if not image_todo_flag:         
        # user_link = f'<a href="https://osu.ppy.sh/users/{osu_score.get("user_id")}">{country_flag} <b>{rank_text}</b></a>\n\n'  

        map_id = map.get('beatmap_id')
        map_url = f"https://osu.ppy.sh/b/{map_id}"
        map_text = f'<a href="{map_url}">{beatmap_escaped} [{stars:.2f}★]</a> {try_text}\n\n'
        # spacer = '\n'
    else:        
        # user_link = f''  

        map_text = f''
        # spacer = '\n'

    bpm, ar, od, cs, hp = apply_mods_to_stats(
        expected_bpm, base_ar, base_od, base_cs, base_hp,
        speed_multiplier=speed_multiplier, hr=hr_active, ez=ez_active
    )
    length = int(round(float(map.get('hit_length')) / speed_multiplier))
        

    if lazer: 
        is_stable_client = ""
    else:
        is_stable_client = "(Stable)"        

    mods_lazer = text_format.normalize_plus(mods_str)

    mods_text = f'{mods_lazer}{is_stable_client}'
    combo_text = f'<b>{osu_score.get("max_combo")}x</b>/{perfect_combo}x'

    choke_title = choke_value = "<code>-</code>"
    
    if not rank == "F" and not failed:
        pp_text = f'<b>{pp:.1f}</b>/{perfect_pp:.1f} <s>({max_pp:.1f}pp)</s>'
        pp_text_alt = f'<b>{pp:.2f}</b> <s>({max_pp:.2f})</s>'

        choke_title = 'Чоук'
        choke_value = pp - max_pp
        choke_value = f'{choke_value:.2f}'

        if int(pp) == int(max_pp):
            choke_title = choke_value = "<code>-</code>"
            pp_text_alt = f'<b>{pp:.2f}</b>'
    else:
        if lazer:
            hit300 = osu_score.get("count_300") or 0
            hit100 = osu_score.get("count_100") or 0
            hit50 = osu_score.get("count_50") or 0
            hit_miss = osu_score.get('count_miss') or 0
            max_hits = osu_statistics_max['great']

            hits = hit300 + hit100 + hit50 + hit_miss

            progress = (hits / max_hits) * 100 if max_hits else 0
            pp_text = f'<code>Fail ({progress:.0f}%)</code>  ~<b>{pp:.1f}pp</b> '
            pp_text_alt = f'<code>Фейл ({progress:.0f}%)</code>  ~<b>{pp:.2f}</b> '
        else:
            rank = "F"
            pp_text = f'<code>Fail ~{pp:.1f}pp </code>'
            pp_text_alt = f'<code>Фейл ~{pp:.2f}</code>'

    score_url = f"https://osu.ppy.sh/scores/{osu_api_data.get('id')}"
    score_date = text_format.format_osu_date(osu_api_data.get('date'), today=is_recent)
    map_id = map.get('beatmap_id')
    map_url = f"https://osu.ppy.sh/b/{map_id}"
    status = map.get('status')
    mapper = map.get("mapper")

    # miss, miss_text = osu_score.get('count_miss'), '\n'
    # if miss:
    #     miss_text = f"<b> • {osu_score.get('count_miss')}</b>❌\n"

    # caption = (
    #     f'{user_link}{map_text}<b><i><a href="{score_url}">{rank}</a></i>  {mods_text}   {accuracy_display}</b>    <code>{score_date}</code>{spacer}'
    #     f"{pp_text} • {combo_text}{miss_text}"
    #     f"<code>{text_format.seconds_to_hhmmss(length)} • CS:{cs:g} AR:{ar:g} OD:{od:g} BPM:{bpm:g}</code>\n\n"
    #     f'⦿ <a href="{map_url}">Mapset</a> by {mapper} • {status.capitalize()}  <a href="https://myangelfujiya.ru/weakness/direct?id={map_id}">🔗</a>\n'
    #     )      
 

    iso_time = osu_api_data.get('date')
    unix_time = iso_to_unix(iso_time)

    hit300 = osu_score.get("count_300") or "<code>0</code>"
    hit100 = osu_score.get("count_100") or "<code>0</code>"
    hit50 = osu_score.get("count_50") or "<code>0</code>"
    hit_miss = osu_score.get('count_miss') or 0
    max_hits = osu_statistics_max['great']
    # length_text = text_format.seconds_to_hhmmss(length)

    if hit_miss == 0:
        hit_miss = "<code>0✖️</code>"
    else:
        hit_miss = f"{hit_miss}❌"

    # extra_caption = await get_score_caption(cached_entry)

    sep = "<code>...</code>"

    # preview_url = map.get("preview_url")

    # if preview_url is None:
    #     preview_url = ""
    # else:
    #     preview_url = f'<audio src="{preview_url}"></audio>\n'

    osu_score['score_lazer'] = lazer_data.get("total_score")
    scores = [
        ("1", "score_lazer"),
        ("2", "score_legacy_lazer"),
        ("3", "score_legacy"),
        ("4", "total_score_without_mods"),
    ]

    seen = set()
    result = {}

    for label, field in scores:
        value = osu_score.get(field, 0)

        if value in seen:
            result[label] = "-"
        else:
            seen.add(value)
            result[label] = f"{value:,}"

    caption = f"""   
<h3><a href="https://osu.ppy.sh/users/{osu_score.get("user_id")}">{country_flag} <b>{username}: </b></a>{pp_profile_text_alt}pp <sup>{global_rank_text_alt}</sup><h2>

<tg-collage>
<img src="{map.get('card2x_url')}"/>
</tg-collage>

<details><summary>{map_text}</summary>

| <code>Автор (сет)</code> | <a href="{map_url}">{truncate(mapper)}</a> 🔗 | <code>ID карты</code> | <code>{map_id}</code> |
|:--:|:------------:|:--:|:------------:|
|{map_cs:g}<sub>CS</sub>|{map_ar:g}<sub>AR</sub>|{map_od:g}<sub>OD</sub>|{map_hp:g}<sub>HP</sub>|
| <code>Объекты</code> | {max_hits} | <code>Статус</code> | {status.capitalize()} |

</details>

<h3> <a href="{score_url}">{rank}</a> {mods_text} 〰️ <tg-time unix="{unix_time}" format="r">{score_date}</tg-time></h3>

|<code>Точность</code>|<code>Комбо</code>|<code>PP</code>| 
|:-:|:-:|:-:|
|{accuracy_display}|{combo_text}|{pp_text_alt}|

<details><summary> {sep} {hit_miss} -  {status.capitalize()}</summary>

|{hit300}<sub>300</sub>|{hit100}<sub>100</sub>|{hit50}<sub>50</sub>|{hit_miss}|
|:-:|:-:|:-:|:-:|
|{format_stat("CS", map_cs, cs)}|{format_stat("AR", map_ar, ar)}|{format_stat("OD", map_od, od)}|{format_stat("HP", map_hp, hp)}|
| <code>Макс. PP</code> | {perfect_pp:.2f} | <code>Длина</code> | {text_format.seconds_to_hhmmss(length)} |
| <code>{choke_title}</code> | {choke_value} | <code>BPM</code> | {bpm:g} |

| <code>Лазер</code> | {result['1']} | <code>Стебйл</code> | <u>{result['2']}</u> |
|:--:|:------------:|:--:|:------------:|
| <code>Лазер-CL</code> | {result['3']} | <code>Ссылка</code> | <a href="{score_url}">🔗</a> |
</details>"""

    img_path = None
    if image_todo_flag:
        img_path = await create_beatmap_image(cached_entry)
    
    return img_path, caption


async def send_score(
        update: Update, 
        cached_entry: dict, 
        query=None, 
        img_path=None, 
        is_recent=True,
        reply_markup=None
    ):
    s =  temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(update.effective_user.id), {}) 
    rs_bg_render = user_settings.get("rs_bg_render", False)  
    rs_bg_render = False # for now ...
    img_path, caption = await process_score_and_image(cached_entry, image_todo_flag=rs_bg_render, is_recent=is_recent)

    # link_preview = LinkPreviewOptions(
    #     url=cached_entry.get('map').get('card2x_url'),
    #     is_disabled=False,
    #     prefer_small_media=False,
    #     prefer_large_media=True,
    #     show_above_text=True
    # )

    try:
        if query:
            if img_path:
                with open(img_path, "rb") as f:
                    bio = io.BytesIO(f.read())
                media = InputMediaPhoto(media=bio, caption=caption, parse_mode="HTML")
                await query.edit_message_reply_markup(reply_markup=reply_markup)
                return await query.edit_message_media(media=media)
            else:
                # return await query.edit_message_text(
                #     text=caption,
                #     parse_mode="HTML",
                #     link_preview_options=link_preview,
                #     reply_markup=reply_markup
                # )

                return await edit_rich_message(
                    update.callback_query.message.id,
                    caption,
                    reply_markup=reply_markup
                )
        else:
            if img_path:
                return await update.message.reply_photo(
                    photo=open(img_path, "rb"),
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            else:
                # return await update.message.reply_text(
                #     caption,
                #     parse_mode="HTML",
                #     link_preview_options=link_preview,
                #     reply_markup=reply_markup
                # )                
            
                return await rich_reply(
                    update,
                    caption,
                    reply_markup=reply_markup,
                    message_thread_id=getattr(update.message, "message_thread_id", None)
                )
    except Exception:
        traceback.print_exc()


def iso_to_unix(iso_str: str) -> int:
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return int(dt.timestamp())

def pretty_time(iso_str: str) -> str:
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%d %b %Y %H:%M")

def truncate(text: str, length: int = 6):
    if len(text) <= length:
        return text
    return text[:length] + ".."

def format_stat(name, base, modified):
    if modified > base:
        icon = "🔺"
    elif modified < base:
        icon = "🔻"
    else:
        icon = ""

    return f"{icon}{modified:g}<sub>{name}</sub>"