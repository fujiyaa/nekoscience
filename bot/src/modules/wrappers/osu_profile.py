    


from ..utils.text_format import format_osu_date2
from ..wrappers.userlink_rich import get_rich_userlink



def get_profile_text(user_data):
    
    if isinstance(user_data, dict):
        stats = user_data["statistics"]        

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

        joined = format_osu_date2(user_data['join_date'], "%Y-%m-%d %H:%M:%S", True, "ru")

    else:
        return None             
    
    return f"""
{get_rich_userlink(user_data)}

<tg-collage>
  <img src="{user_data['cover_url']}"/>
</tg-collage>

- ### Макс. рейтинг: <code> #{peak_rank:,}   {peak_date}</code>
</hr>
- ### Игр: <code> {plays:,}</code>   (<code>{hours} ч.</code>)
</hr>
- ### Точность: <code> {accuracy:.2f}%</code> •<code>  </code>Уровень:<code> {level}</code>
</hr>
- ### Медалей: <code> {medals} </code> •<code>  </code>Команда: {team_link}
</hr>
- Зарегистрирован {joined}
"""