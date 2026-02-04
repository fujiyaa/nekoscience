


from telegram import LinkPreviewOptions

from ....actions.messages import safe_edit_query
from ....utils.text_format import normalize_plus, format_osu_date
from ....utils.calculate import caclulte_cached_entry
from ....wrappers.user import get_user_link
from ....wrappers.mapset import get_map_text, get_mapset_link



async def send_best_scores(update, scores: dict = [], limit: int = 5):   
    
    user_link = get_user_link(scores[0])
    scores_text = ""
    
    is_recent = False
    
    for i, cached_entry in enumerate(scores[:limit]):
        text = ""

        if not cached_entry['state']['calculated']:
            await caclulte_cached_entry(cached_entry)

        osu_api_data =      cached_entry['osu_api_data']
        osu_score =         cached_entry['osu_score']
        neko_api_calc =     cached_entry['neko_api_calc']
        lazer_data =        cached_entry['lazer_data']
        state =             cached_entry['state']

        pp = neko_api_calc.get("pp")
        max_pp = neko_api_calc.get("no_choke_pp")
        perfect_pp = neko_api_calc.get("perfect_pp")
        perfect_combo = neko_api_calc.get("perfect_combo")


        #temp pp fix
        pp = pp if not isinstance(osu_score.get("pp"), (int, float)) or osu_score.get("pp") <= 0 else osu_score.get("pp")
    

        lazer = state.get('lazer')
        accuracy = osu_score.get('accuracy')
        
        if lazer:                
            rank = lazer_data.get('rank') 
        else:            
            rank = osu_api_data.get('rank_legacy')     

        accuracy_display = round(accuracy * 100, 2)
        accuracy_display = (f"{accuracy_display}%")

        mods_str = osu_score.get("mods", "")
        mods_text = normalize_plus(mods_str)
      
          
        if lazer: 
            is_cl = ""
        else:
            is_cl = '(Stable)'
        
        mods_lazer = normalize_plus(mods_str)
        mods_text = f'{mods_lazer}{is_cl}'
        
        if perfect_combo and i == 0:
            combo_text = f'<b>{osu_score.get("max_combo")}x</b>/{perfect_combo}x • '
        else: 
            combo_text = f'<b>{osu_score.get("max_combo")}x</b> • '

        if perfect_pp and i == 0:
            pp_text = f'• <b>{pp:.1f}</b>/{perfect_pp:.1f} <s>({max_pp:.1f}pp)</s>  • '
        else: 
            pp_text = f'• <b>{pp:.1f}pp</b> • '

        score_url = f"https://osu.ppy.sh/scores/{osu_api_data.get('id')}"
        score_date = format_osu_date(osu_api_data.get('date'), today=is_recent)        

        miss, miss_text = osu_score.get('count_miss'), ''
        if miss:
            miss_text = f"<b>{osu_score.get('count_miss')}</b>❌"
        
        score_date = format_osu_date(osu_api_data.get('date'), today=False)         ###
        
        if i == 1: 
            text += f'\n'
        if i == 0:
            text += f'<u>Personal Best:</u> '
            text += f'<a href="{score_url}"><b>{rank} {mods_text}  </b>({accuracy_display})</a>    <code>{score_date}</code>\n'
            text += f"{pp_text}{combo_text}{miss_text}\n"
        
        else:
            text += f'<code>#{i+1}</code>  '
            text += f'<a href="{score_url}"><b>{rank} {mods_text} </b>({accuracy_display})</a> {combo_text}{miss_text}\n'
            text += f'<code>{pp_text}{score_date}</code>\n'
                            
        scores_text += text


    if limit < len(scores):
        scores_text += f'<code>and {len(scores) - limit} more...</code>\n'

    map = await get_map_text(scores[0])
    mapset = await get_mapset_link(scores[0])

    caption = (
        f'{user_link}\n'
        f'\n'
        f'{map}\n'
        f'\n' 
        f'{scores_text}'
        f'\n'       
        f'{mapset}'
    )

    link_preview = LinkPreviewOptions(
        url=scores[0].get('map').get('card2x_url'),
        is_disabled=False,
        prefer_small_media=False,
        prefer_large_media=True,
        show_above_text=True
    )

    try:
        return await safe_edit_query(
            query=update,
            text=caption,
            parse_mode="HTML",
            link_preview_options=link_preview
        )

    except:       
        return await update.message.reply_text(
            caption,
            parse_mode="HTML",
            link_preview_options=link_preview
        )
