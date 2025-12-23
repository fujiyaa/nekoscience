


import io 
import html
import temp
import traceback
from telegram import Update, InputMediaPhoto, LinkPreviewOptions

from ..external import localapi
from ..utils import text_format
from ..external.osu_http import beatmap
from ..utils.osu_conversions import get_mods_info, apply_mods_to_stats
from ..wrappers.beatmap import create_beatmap_image

from config import USER_SETTINGS_FILE



# универсальная для команд где нужен скор
async def process_score_and_image(score, image_todo_flag = False, is_recent=True):       
    mods_str = score.get("mods", "")
    speed_multiplier, hr_active, ez_active = get_mods_info(mods_str)

    path, base_values = await beatmap(score['beatmap']['id'])

    base_values["ar"] = score.get("ar", 5) if base_values.get("ar") is None else base_values["ar"]
    
    base_ar = score.get("DA_values", {}).get("approach_rate", base_values["ar"])
    base_cs = score.get("DA_values", {}).get("circle_size", base_values["cs"])
    base_od = score.get("DA_values", {}).get("overall_difficulty",base_values["od"])
    base_hp = score.get("DA_values", {}).get("drain_rate", base_values["hp"])

    score_stats = score.get("score_stats", score.get("statistics"))
    misses = score.get('count_miss', score.get("statistics", {}).get("count_miss", 0))

    mods_text = text_format.normalize_no_plus(mods_str)

    mods_str = score.get("mods", "")
  
    #neko API 
    payload = {
        "map_path": str(score['beatmap']['id']), 
        
        "n300": score_stats.get("count_300", score_stats.get("great", None)),
        "n100": score_stats.get("count_100", score_stats.get("ok", None)),
        "n50": score_stats.get("count_50", score_stats.get("meh", None)),
        "misses": int(misses),                   
        
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

          
    #temp pp fix
    pp = pp if not isinstance(score.get("pp"), (int, float)) or score.get("pp") <= 0 else score.get("pp")


    accuracy = round(score['accuracy'] * 100, 2)
    accuracy_display = (
        f"{accuracy}%"
        if isinstance(score['accuracy'], (int, float))
        else "N/A"
    )    
    if score['lazer']:   
        if accuracy == 100:
            score["rank"] = 'SS'
        elif accuracy >= 90:
            if (misses == 0) and (accuracy >= 95):
                score["rank"] = 'S'
            else:
                score["rank"] = 'A'
        elif accuracy >= 80:
            score["rank"] = 'B'
        elif accuracy >= 70:
            score["rank"] = 'C'
        else:
            score["rank"] = 'D'
    
    spacer = '\n\n'
    user_link = ''
    if not image_todo_flag: 
        username = score.get("username") or score.get("user", {}).get("username")
        pp_text = f"{score.get('total_pp')}" if score.get("pp") else "0"
        global_rank_text = f"(#{score.get('global_rank'):,}" if score.get("global_rank") else "(#????"        
        rank_text = f"{username}: {pp_text}pp {global_rank_text})"
        country_flag = text_format.country_code_to_flag(country_code = score.get("country_code") or score.get("user", {}).get("country", {}).get("code"))
        user_link = f'<a href="https://osu.ppy.sh/users/{score["user"]["id"]}">{country_flag} <b>{rank_text}</b></a>\n\n'  

        beatmap_escaped = html.escape(score["beatmap_full"])
        map_text = f'<a href="{score["url"]}">{beatmap_escaped} [{stars:.2f}★]</a>\n\n'
        spacer = '\n'
    else:
        username = score.get("username") or score.get("user", {}).get("username")
        pp_text = f"{score.get('total_pp')}" if score.get("pp") else "0"
        global_rank_text = f"(#{score.get('global_rank'):,}" if score.get("global_rank") else "(#????"        
        rank_text = f"{username}: {pp_text}pp {global_rank_text})"
        country_flag = text_format.country_code_to_flag(country_code = score.get("country_code") or score.get("user", {}).get("country", {}).get("code"))
        user_link = f''  

        beatmap_escaped = html.escape(score["beatmap_full"])
        map_text = f''
        spacer = '\n'

    bpm, ar, od, cs, hp = apply_mods_to_stats(
        expected_bpm, base_ar, base_od, base_cs, base_hp,
        speed_multiplier=speed_multiplier, hr=hr_active, ez=ez_active
    )
    length = int(round(float(score['hit_length']) / speed_multiplier))
    
    is_cl = 'CL'
    mods_lazer = text_format.normalize_plus(mods_str)
    if str(mods_lazer) == '':
        is_cl = '+CL'   
    if score['lazer']: 
        is_cl = ""
    mods_text = f'{mods_lazer}{is_cl}'
    combo_text = f'<b>{score["max_combo"]}x</b>/{perfect_combo}x'
    map_id = score.get("beatmap", {}).get("id", 0)    
    set_id = score.get("beatmap", {}).get("beatmapset_id", 0) 
    pp_text = f'<b>{pp:.1f}</b>/{perfect_pp:.1f} <s>({max_pp:.1f}pp)</s>'
    caption = (
                 f'{user_link}{map_text}<b><i><a href="{score["url"]}">{score["rank"]}</a></i>  {mods_text}   {accuracy_display}</b>    <code>{text_format.format_osu_date(score["date"], today=is_recent)}</code>{spacer}'
                 f"{pp_text} • {combo_text} • <b>{score['count_miss']}</b>❌\n"
                 f"<code>{text_format.seconds_to_hhmmss(length)} • CS:{cs} AR:{ar} OD:{od} BPM:{bpm}</code>\n\n"
                 f'⦿ <a href="{score["url"]}">Mapset</a> by {score["mapper"]} • {score["status"].capitalize()}  <a href="https://myangelfujiya.ru/darkness/direct?id={map_id}&set_id={set_id}">🔗</a>\n'
             )          

    img_path = None
    if image_todo_flag:
        score["sr"] = stars
        img_path = await create_beatmap_image(score)
    
    return img_path, caption


async def send_score( update: Update, score: dict, user_id: str,  session: dict,  message_id: int, query=None,  show_buttons=True, img_path=None, is_recent=True):
    s =  temp.load_json(USER_SETTINGS_FILE, default={})
    user_settings = s.get(str(update.effective_user.id), {}) 
    rs_bg_render = user_settings.get("rs_bg_render", False)  
    img_path, caption = await process_score_and_image(score, image_todo_flag=rs_bg_render, is_recent=is_recent)

    link_preview = LinkPreviewOptions(
        url=score.get('card2x_url'),
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