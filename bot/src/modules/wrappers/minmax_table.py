


from ..systems.translations import DEFAULT_SCORES_PROP as SP



def get_minmax_table(table_data, lang):    

    def format_cell(value, score_id, formatter=None):
        if value == " " or score_id == " ":
            return " "

        if formatter:
            value_str = formatter(value)
        else:
            try:
                value = float(value)
                value_str = f"{value:.2f}"
            except (ValueError, TypeError):
                value_str = str(value)

        return f"<a href='https://osu.ppy.sh/scores/{score_id}'>{value_str}</a>"

    formatters = {
        SP.get('Length')[lang]: format_time
    }

    lines = []
    for key, values in table_data.items():
        (min_v, min_id), (max_v, max_id) = values

        formatter = formatters.get(key)

        min_cell = format_cell(min_v, min_id, formatter)
        max_cell = format_cell(max_v, max_id, formatter)

        line = f"{key}     {min_cell} | {max_cell}"
        lines.append(line)

    return "\n".join(lines)
    
def format_time(seconds):
    if isinstance(seconds, str):
        return seconds
    m, s = divmod(int(round(seconds)), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
