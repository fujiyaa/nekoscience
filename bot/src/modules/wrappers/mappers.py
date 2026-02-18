    


from ..utils.text_format import country_code_to_flag
from collections import defaultdict



def get_mappers_text(user_data, best_pp):
    
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

        return f"{user_link}\n\n<pre>{table_text}</pre>"