


from telegram import Update, MessageEntity

from ....actions.messages import safe_send_message, safe_edit_query



async def send(update: Update, stats_batch: dict = None, caption: str = ''):
    if not stats_batch:
        try:
            await safe_edit_query(
                update.callback_query, 
                "Нет данных",
                parse_mode="HTML"
            )
        except:
            await safe_send_message(
                update,
                "Нет данных",
                parse_mode="HTML"
            )     
        return
    
    try:
        entities = [
            MessageEntity(
                type="expandable_blockquote",
                offset=0,                     
                length=len(caption)+4     
            )
        ]        
        
        await safe_edit_query(
            update.callback_query, 
            caption,
            parse_mode="HTML",
            entities=entities
        )
    except:
        await safe_send_message(
            update,
            caption,
            parse_mode="HTML",
            # reply_markup=pagination
        )         