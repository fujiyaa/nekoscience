


# {
#     message_id: {
#         user_id: "pos" | "neg"
#     }
# }

VOTE_CACHE = {}



def register_vote(message_id: int, user_id: int, vote: str) -> bool:

    if message_id not in VOTE_CACHE:
        VOTE_CACHE[message_id] = {}

    user_votes = VOTE_CACHE[message_id]

    if user_id in user_votes:
        if user_votes[user_id] == vote:
            return False
        else:
            user_votes[user_id] = vote
            return True

    user_votes[user_id] = vote
    return True

def get_vote_counts(message_id: int) -> tuple[int, int]:
    if message_id not in VOTE_CACHE:
        return 0, 0

    votes = VOTE_CACHE[message_id].values()
    positive = sum(1 for v in votes if v == "pos")
    negative = sum(1 for v in votes if v == "neg")

    return positive, negative