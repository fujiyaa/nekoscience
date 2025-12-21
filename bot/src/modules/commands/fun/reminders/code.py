


import random
import string



def generate_unique_code(existing_codes, length=8):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if code not in existing_codes:
            return code