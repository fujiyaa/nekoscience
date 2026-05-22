


def force_finish_match(match: dict, leaver_osu_id: str) -> dict:
    creator_osu_id = str(match.get('creator', {}).get('osu_id'))
    member_osu_id = str(match.get('member', {}).get('osu_id'))

    if leaver_osu_id == creator_osu_id:
        leaver_role = 'creator'
        winner_role = 'member'
    elif leaver_osu_id == member_osu_id:
        leaver_role = 'member'
        winner_role = 'creator'
    else:
        return None

    match.setdefault('state', {})
    match.setdefault('submit_state', {})
    match.setdefault('submit_result', {})

    match['state']['elo_calculated'] = False
    
    match['state']['finished'] = True
    match['state']['winner'] = winner_role

    match['submit_state'][creator_osu_id and 'creator' or 'member'] = True
    match['submit_state'][winner_role] = True

    match['submit_result'][winner_role] = 1.0
    match['submit_result'][leaver_role] = 0.0

    return match