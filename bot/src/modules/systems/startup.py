


import logging
import atexit
import glob
import os

from ...config import BOT_DIR, TEMP_DIR



def startup():    
    cleanup_flags()
    
    atexit.register(cleanup_temp)

    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO  
    )

    return logging.getLogger(__name__)
    
def cleanup_temp():
    for f in glob.glob(os.path.join(TEMP_DIR, "*.png")):
        try:
            os.remove(f)
        except:
            pass

def cleanup_flags():
    flags_dir = os.path.join(BOT_DIR, "stats", "flags")
    
    if os.path.exists(flags_dir):
        for f in os.listdir(flags_dir):
            try:
                os.remove(os.path.join(flags_dir, f))
            except Exception:
                pass
    else:
        os.makedirs(flags_dir, exist_ok=True)      


