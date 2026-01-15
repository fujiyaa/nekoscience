


import asyncio

search_limit = asyncio.Semaphore(5)



async def _check_member(bot, chat_id, uid):
    async with search_limit:
        try:
            member = await bot.getChatMember(chat_id, uid)
            if member.status in ["member", "administrator", "creator"]:
                return uid, True
            return uid, False
        except Exception:
            return uid, None

async def check_all(bot, chat_id, user_ids):
    """   
    Какие тг id есть в группе, из osu_verified 
    
    :param bot: тг бот
    :param chat_id: id группы
    :param user_ids: список из osu_verified 

    results → list[(uid, status)]
    """
    tasks = [asyncio.create_task(_check_member(bot, chat_id, uid)) for uid in user_ids]
    results = await asyncio.gather(*tasks)
    
    return results
