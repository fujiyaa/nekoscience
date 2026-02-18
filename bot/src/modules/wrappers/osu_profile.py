    


from ..utils.text_format import country_code_to_flag, format_osu_date2



def get_profile_text(user_data):
    
    if isinstance(user_data, dict):                
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

        hours = user_data['statistics']['play_time'] // 3600
        plays = stats.get('play_count') if stats.get('play_count') else "0"                
        accuracy = stats.get('hit_accuracy') if stats.get('hit_accuracy') else "0"
        medals = len(user_data['user_achievements'])
        
        level_data = stats.get('level', {})
        current = level_data.get('current', 0)
        progress = level_data.get('progress', 0)

        level = current + progress / 100

        try:
            team = user_data['team']['short_name']
            team_url = f"https://osu.ppy.sh/teams/{user_data['team']['id']}"
            team_link = f'<a href="{team_url}">{team}</a>'
        except:
            team_link = '✖️' 

        try:  
            peak_rank = user_data['rank_highest']['rank']     
            peak_date = format_osu_date2(user_data['rank_highest']['updated_at'], "%d.%m.%Y", flag=False)
        except:            
            peak_rank = 0           
            peak_date = '-'

        joined = format_osu_date2(user_data['join_date'], "%Y-%m-%d %H:%M:%S")

        user_id = f"https://osu.ppy.sh/users/{user_data['id']}"
        user_link = f'<a href="{user_id}">{country_flag} <b>{rank_text}</b></a>'
    else:
        return None             
    
    return (
        f"{user_link}\n\n"
        f"Accuracy: <code> {accuracy:.2f}%</code>  •  Level:<code> {level}</code>\n"
        f"Playcount: <code> {plays:,}</code>   (<code>{hours} hrs</code>)\n"
        f"Medals: <code> {medals} </code> •  Team: {team_link}\n"
        f"Peak rank: <code> #{peak_rank:,}</code>   {peak_date}\n\n"
        f"⦿ Joined {joined}\n\n"
    ) 