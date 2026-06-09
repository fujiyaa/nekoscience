


DB_PATH = "ecos.db"

UPGRADES_PAGE_SIZE = 2
SHOP_PAGE_SIZE = 6
INVENTORY_PAGE_SIZE = 8
STORAGE_PAGE_SIZE = 8

MAX_NEGATIVE_BALANCE = -500

def level_multiplier(level):
    return 1 + (level * 0.04)

def xp_required(level):
    return int(100 * (level ** 2.0))

# def old_xp_required(level):
#     return level * 100