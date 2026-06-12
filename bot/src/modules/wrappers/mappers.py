    


from .userlink_rich import get_rich_userlink

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

        top_mappers = sorted_mappers[:100]

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

        top5 = top_mappers[:5]
        rest = top_mappers[5:]

        top5_rows = "\n".join(
            f"| {mapper} | {data['pp_sum']:.2f} | {data['count']} |"
            for mapper, data in top5
        )

        rest_rows = "\n".join(
            f"| {mapper} | {data['pp_sum']:.2f} | {data['count']} |"
            for mapper, data in rest
        )
        table_title ="Маппер | PP | кол-во в топ100 |"
        details = ""
        if rest:
            details = f"""
<details>
<summary>...ещё {len(rest)}</summary>

{table_title}
|:-------|---:|--:|
{rest_rows}

</details>
"""

        return f"""
{get_rich_userlink(user_data)}

{table_title}
|:-------|---:|--:|
{top5_rows}

{details}
"""