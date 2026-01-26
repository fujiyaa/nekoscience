from telegram import Update, Message
from typing import Optional, Dict, Any
from ..systems import context_db as db

EXPIRATION = 30 * 24 * 3600


def _extract_ids(obj: Update | Message, reply: bool = False) -> Dict[str, Optional[int]]:
   
    if isinstance(obj, Update):
        msg = obj.effective_message
        chat = obj.effective_chat
    elif isinstance(obj, Message):
        msg = obj
        chat = obj.chat
    else:
        raise TypeError(f"Unsupported type: {type(obj)}")

    if reply and getattr(msg, "reply_to_message", None):
        target_msg_id = msg.reply_to_message.message_id
    else:
        target_msg_id = msg.message_id

    return {
        "chat_id": chat.id,
        "topic_id": getattr(msg, "message_thread_id", None),
        "message_id": target_msg_id,
        "is_supergroup": chat.type.endswith("group")
    }


def set_message_context(obj: Update | Message,
                  *,
                  ttl=EXPIRATION,
                  reply=False,
                  **metadata):
    ids = _extract_ids(obj, reply=reply)
    if ids["topic_id"] is None:
        ids["topic_id"] = -1

    db.cache_message(
        is_supergroup=ids["is_supergroup"],
        chat_id=ids["chat_id"],
        topic_id=ids["topic_id"],
        message_id=ids["message_id"],
        metadata=metadata,
        ttl=ttl
    )

    db.cleanup_expired()


def get_message_context(obj: Update | Message, reply: bool = False) -> Optional[Dict[str, Any]]:
  
    ids = _extract_ids(obj, reply=reply)

    if reply:
        data = db.find_by_message_id(ids["message_id"])
    else:
        data = db.find_recent(chat_id=ids["chat_id"], topic_id=ids["topic_id"])
    
    return data
