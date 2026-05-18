


import logging
import logging.handlers
import queue



log_queue = queue.Queue()
queue_handler = logging.handlers.QueueHandler(log_queue)

logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)
logger.addHandler(queue_handler)

file_handler = logging.FileHandler("unranked_callback.log", encoding="utf-8")

listener = logging.handlers.QueueListener(
    log_queue,
    file_handler
)

listener.start()

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)
file_handler.setFormatter(formatter)
