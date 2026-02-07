#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import logging

from pyrogram import Client


class InlineHandler(logging.StreamHandler):
    def __init__(self, client: Client):
        ...


def load(level: logging.NOTSET) -> logging.Logger:  # type: ignore
    format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(funcName)s: %(lineno)d - %(message)s",
        "%m-%d %H:%M:%S")

    logger = logging.getLogger()
    logger.handlers = []
    logger.setLevel(level)

    console = logging.StreamHandler()
    console.setFormatter(format)
    logger.addHandler(console)

    # telegram_handler = InlineHandler(client)
    # logger.addHandler(telegram_handler)
    # telegram_handler.setFormatter(format)

    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    return logger
