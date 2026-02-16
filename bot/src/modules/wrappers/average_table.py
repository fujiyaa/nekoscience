


from ..systems.translations import DEFAULT_SCORES_PROP as SP



def get_average_table(table_data, lang):
    formatted_table_data = {}
    for key, values in table_data.items():
        formatted_values = []
        for v in values:
            if isinstance(v, str):
                formatted_values.append(v)
            elif key == "Length":
                formatted_values.append(_format_time(v))
            elif isinstance(v, float):
                formatted_values.append(f"{v:.2f}")
            else:
                formatted_values.append(str(v))
        formatted_table_data[key] = formatted_values

    headers = [
        "", 
        SP.get('Minimum')[lang], 
        SP.get('Average')[lang], 
        SP.get('Maximum')[lang]
    ]
    rows = [[key, *values] for key, values in formatted_table_data.items()]

    col_widths = [
        max(len(str(headers[i])), max(len(str(row[i])) for row in rows))
        for i in range(len(headers))
    ]

    def fmt_row(row):
        return " | ".join(
            str(row[i]).ljust(col_widths[i]) if i == 0 else str(row[i]).center(col_widths[i])
            for i in range(len(row))
        )

    header_line = fmt_row(headers)
    sep_line = "-+-".join("-" * w for w in col_widths)
    table_lines = [header_line, sep_line] + [fmt_row(row) for row in rows]

    table = "\n".join(table_lines)

    return table

def _format_time(seconds):
    if isinstance(seconds, str):
        return seconds
    m, s = divmod(int(round(seconds)), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
