#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from .handlers import register_handlers


class Inline:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot)

    async def start(self):
        register_handlers(self.dp)
        logging.info("Inline bot is loaded.")
        asyncio.ensure_future(self.dp.start_polling())

    async def stop(self):
        await self.bot.close()
