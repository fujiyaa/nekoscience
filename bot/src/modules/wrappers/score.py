


import io 
import html
import temp
import traceback
from telegram import Update, InputMediaPhoto, LinkPreviewOptions

from ..utils import text_format
from ..external.osu_http import beatmap
from ..utils.osu_conversions import get_mods_info, apply_mods_to_stats
from ..wrappers.beatmap import create_beatmap_image
from ..utils.calculate import caclulte_cached_entry

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
    
    acc = osu_score.get('accuracy')

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
    global_rank_text = f"(#{user.get('global_rank'):,}" if user.get("global_rank") else "(#????"        
    rank_text = f"{username}: {pp_text}pp {global_rank_text})"
    country_flag = text_format.country_code_to_flag(country_code = user.get("country_code")) 

    beatmap_escaped = html.escape(map.get('beatmap_full'))
    
    try_count, _failed = osu_score.get('try_count'), osu_score.get('failed')
    try_text = ''
    if try_count > 1:
        try_text = f"<i><b>- Try #{try_count}</b></i>"

    if not image_todo_flag:         
        user_link = f'<a href="https://osu.ppy.sh/users/{osu_score.get("user_id")}">{country_flag} <b>{rank_text}</b></a>\n\n'  

        map_id = map.get('beatmap_id')
        map_url = f"https://osu.ppy.sh/b/{map_id}"
        map_text = f'<a href="{map_url}">{beatmap_escaped} [{stars:.2f}★]</a> {try_text}\n\n'
        spacer = '\n'
    else:        
        user_link = f''  

        map_text = f''
        spacer = '\n'

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

    if not rank == "F":
        pp_text = f'<b>{pp:.1f}</b>/{perfect_pp:.1f} <s>({max_pp:.1f}pp)</s>'
    else:
        hit300 = osu_score.get("count_300") or 0
        hit100 = osu_score.get("count_100") or 0
        hit50 = osu_score.get("count_50") or 0
        hit_miss = osu_score.get('count_miss') or 0
        max_hits = osu_statistics_max['great']

        hits = hit300 + hit100 + hit50 + hit_miss

        progress = (hits / max_hits) * 100 if max_hits else 0

        pp_text = f'<code>Fail ({progress:.0f}%)</code>  ~<b>{pp:.1f}pp</b> '
    score_url = f"https://osu.ppy.sh/scores/{osu_api_data.get('id')}"
    score_date = text_format.format_osu_date(osu_api_data.get('date'), today=is_recent)
    map_id = map.get('beatmap_id')
    map_url = f"https://osu.ppy.sh/b/{map_id}"
    status = map.get('status')
    mapper = map.get("mapper")

    miss, miss_text = osu_score.get('count_miss'), '\n'
    if miss:
        miss_text = f"<b> • {osu_score.get('count_miss')}</b>❌\n"

    caption = (
        f'{user_link}{map_text}<b><i><a href="{score_url}">{rank}</a></i>  {mods_text}   {accuracy_display}</b>    <code>{score_date}</code>{spacer}'
        f"{pp_text} • {combo_text}{miss_text}"
        f"<code>{text_format.seconds_to_hhmmss(length)} • CS:{cs:g} AR:{ar:g} OD:{od:g} BPM:{bpm:g}</code>\n\n"
        f'⦿ <a href="{map_url}">Mapset</a> by {mapper} • {status.capitalize()}  <a href="https://myangelfujiya.ru/darkness/direct?id={map_id}">🔗</a>\n'
        )          
    # &set_id={set_id} вырезано из ссылки директа

    img_path = None
    if image_todo_flag:
        img_path = await create_beatmap_image(cached_entry)
    
    return img_path, caption


async def send_score( update: Update, cached_entry: dict, user_id: str,  session: dict,  message_id: int, query=None,  show_buttons=True, img_path=None, is_recent=True):
    s =  temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(update.effective_user.id), {}) 
    rs_bg_render = user_settings.get("rs_bg_render", False)  
    rs_bg_render = False # for now ...
    img_path, caption = await process_score_and_image(cached_entry, image_todo_flag=rs_bg_render, is_recent=is_recent)

    link_preview = LinkPreviewOptions(
        url=cached_entry.get('map').get('card2x_url'),
        is_disabled=False,
        prefer_small_media=False,
        prefer_large_media=True,
        show_above_text=True
    )

    try:
        if query:
            if img_path:
                with open(img_path, "rb") as f:
                    bio = io.BytesIO(f.read())
                media = InputMediaPhoto(media=bio, caption=caption, parse_mode="HTML")
                await query.edit_message_media(media=media)
            else:
                await query.edit_message_text(
                    text=caption,
                    parse_mode="HTML",
                    link_preview_options=link_preview
                )
        else:
            if img_path:
                return await update.message.reply_photo(
                    photo=open(img_path, "rb"),
                    caption=caption,
                    parse_mode="HTML",
                )
            else:
                return await update.message.reply_text(
                    caption,
                    parse_mode="HTML",
                    link_preview_options=link_preview
                )
    except Exception:
        traceback.print_exc()