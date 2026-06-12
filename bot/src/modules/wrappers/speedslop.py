    


from .userlink_rich import get_rich_userlink

from config import SPEEDSLOP_IDS



def get_speedslop_text(user_data, best_pp):
    
    if isinstance(best_pp, list) and best_pp:
              
        total = len(best_pp)
        counter = 0
        total_weighted_pp = 0
        speedslop_weighted_pp = 0

        for score in best_pp:
            beatmap_id = score.get("beatmap_id")
            pp = float(score.get("pp", 0))
            weight_percent = float(score.get("weight_percent", 0))

            weighted_pp = pp * (weight_percent / 100)
            total_weighted_pp += weighted_pp

            if beatmap_id and beatmap_id in SPEEDSLOP_IDS:
                counter += 1
                speedslop_weighted_pp += weighted_pp

        speedslop_percent = (counter / total) * 100 if total else 0

        speedslop_weighted_percent = (
            (speedslop_weighted_pp / total_weighted_pp) * 100
            if total_weighted_pp else 0
        )

        def percent_emoji(p):
            if p < 1:
                return '✅'
            elif p < 20:
                return '🟢'
            elif p < 30:
                return '🟡'
            elif p < 50:
                return '🟠'
            elif p < 70:
                return '❗️'
            else:
                return '‼️'

        row1_emoji = percent_emoji(speedslop_percent)
        row2_emoji = percent_emoji(speedslop_weighted_percent)

        gwb_url = "https://docs.google.com/spreadsheets/d/1YEbQv9Jpe2ORh4ZHNIZmkeF2fvHku6t2H1LkAUbM06M/edit?gid=1661256767#gid=1661256767"

        return f"""
{get_rich_userlink(user_data)}

| Аимслоп | N | % | ✓ |
|:--------|--:|--:|:-:|
| Карт в топ100 | <b>{counter}</b><code>/{total}</code> | {speedslop_percent:.0f}% | {row1_emoji} |
| PP спидслопа | <b>{speedslop_weighted_pp:.0f}</b>pp | {speedslop_weighted_percent:.0f}% | {row2_emoji} |

<details>
- <b>Карт в топ100</b> - количество из топ100 игрока, спидслоп определяется по <a href="{gwb_url}"><b>Таблице 🔗</b></a>
- <b>PP слопа</b> - сумма скоров, которые вошли в спидслоп список (сохраняется оригинальное взвешивание)
- Чем больше спидслопа тем хуже эмодзи.
</details>
"""