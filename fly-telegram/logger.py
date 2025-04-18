#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import logging
import threading

from pyrogram import Client
from pyrogram.errors import exceptions
from rich.logging import RichHandler


class InlineHandler(logging.StreamHandler):
    def __init__(self, client: Client):
        ...


def load(level) -> logging.Logger:
    format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(funcName)s: %(lineno)d - %(message)s",
        "%m-%d %H:%M:%S")

    logger = logging.getLogger()
    logger.handlers = [RichHandler()]
    logger.setLevel(level)

    # telegram_handler = InlineHandler(client)
    # logger.addHandler(telegram_handler)
    # telegram_handler.setFormatter(format)

    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    return logger
