#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the CC-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import logging

from pyrogram import idle

from . import logger
from .auth import Auth
from .fileswatcher import FilesWatcher
from .inline import inline
from .loader import Loader
from .utils import logo

try:
    import uvloop

    uvloop.install()
except Exception:
    pass


class Userbot:
    def __init__(self):
        self.auth = Auth()
        self.loader = Loader()
        self.loop = asyncio.get_event_loop()

        self.levels = {
            "info": logging.INFO,
            "debug": logging.DEBUG,
            "error": logging.ERROR,
            "warning": logging.WARNING
        }

    async def amain(self, web: bool = True) -> bool:
        """
        async userbot process
        for setting client, loader and etc.
        """
        client, me = await self.auth.load(web)

        await client.initialize()
        await client.dispatcher.start()

        logging.info(f"Started on the {me.first_name}")

        if not client.me:
            client.me = me

        client.loader = self.loader  # type: ignore

        watcher = FilesWatcher(client)
        await watcher.watch()

        await inline.start(client)

        await self.loader.load_all(client)

        await idle()
        return True

    def main(self, level: str = "info", web: bool = True) -> None:
        """
        sync userbot process
        for logo, logger and start async
        """

        print(logo)
        logger.load(self.levels.get(level.lower()))

        try:
            self.loop.run_until_complete(self.amain(web))
        except KeyboardInterrupt:
            print("stopping...")


userbot = Userbot()
