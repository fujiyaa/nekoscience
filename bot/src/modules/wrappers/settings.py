


def get_settings_text(
    text, 
    name, 
    alter_name_flag: bool = False
):
    if alter_name_flag:
        return f"""
#### {text} {name}
"""
    else:
        return f"""
{name}
#### {text}
"""