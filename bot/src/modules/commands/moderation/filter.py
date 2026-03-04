


from config import TARGET_CHAT_ID

CHAT_SETTINGS = {
    TARGET_CHAT_ID: {
        "VOTE_LIMIT": 4,
    },
    -1003045768012: {
        "VOTE_LIMIT": 5,
    },
}



def is_allowed_chat(update) -> bool:
    return update.effective_chat.id in CHAT_SETTINGS


def get_vote_limit(update) -> int:
    chat_id = update.effective_chat.id
    return CHAT_SETTINGS.get(chat_id, {}).get("VOTE_LIMIT", 3)