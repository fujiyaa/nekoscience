def get_fire_text(
    period_text,
    days,
    total_scores,
    filtered_scores,
    raw_pp,
    weighted_pp,
    user_total_pp
):
    if total_scores is None:
        total_scores = 0

    active_count = len(filtered_scores)
    active_per_day = active_count / days if days else 0

    active_percent = (active_per_day / 1.0) * 100
    weighted_percent = (weighted_pp / user_total_pp) * 100 if user_total_pp else 0
    # raw_percent = (raw_pp / weighted_pp) * 100 if weighted_pp else 0

    def activity_emoji(p):
        if p < 2:
            return "💀"
        if p < 4:
            return "❗️"
        elif p < 8:
            return "🔴"
        elif p < 16:
            return "🟠"
        elif p < 20:
            return "🟡"
        else:
            return "🟢"

    def contribution_emoji(p):
        if p < 2:
            return "💀"
        if p < 4:
            return "❗️"
        elif p < 8:
            return "🔴"
        elif p < 16:
            return "🟠"
        elif p < 20:
            return "🟡"
        else:
            return "🟢"

    return f"""
| Костёр ({period_text}) | N | % | ✓ |
|:--------|--:|:-:|:-:|
| cкоров/день | <b>{active_count}</b><code>/{days}</code> | {active_percent:.0f}% | {activity_emoji(active_percent)} |
| PP костра | <b>{weighted_pp:.0f}</b>pp | {weighted_percent:.0f}% | {contribution_emoji(weighted_percent)} |
"""