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
from .inline import Inline
from .loader import Loader
from .logger import InlineHandler
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
        self.inline = Inline()

        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        self.levels = {"info": logging.INFO, "debug": logging.DEBUG, "error": logging.ERROR, "warning": logging.WARNING}

    async def amain(
        self,
        web: bool = True,
        token: str = None,
        qr: bool = False,
    ) -> bool:
        """
        async userbot process
        for setting client, loader and etc.

        Args:
            web (bool): Login with webUI or not
            token (str): Inline bot token
            qr (bool): Login via QR code

        Returns:
            bool: if runned userbot
        """
        client, me = await self.auth.load(web, qr)

        await client.initialize()
        await client.dispatcher.start()

        logging.info(f"Started on the {me.first_name}")

        if not client.me:
            client.me = me

        try:
            telegram_handler = InlineHandler(client)
            telegram_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(funcName)s: %(lineno)d - %(message)s", "%m-%d %H:%M:%S"
                )
            )
            logging.getLogger().addHandler(telegram_handler)
        except Exception:
            pass

        client.loader = self.loader  # type: ignore
        client.inline = self.inline  # type: ignore

        watcher = FilesWatcher(client)
        await watcher.watch()

        await self.inline.start(client, token)

        await self.loader.load_all(client)

        try:
            await idle()
        finally:
            await client.stop()

    def main(
        self,
        level: str = "info",
        web: bool = True,
        token: str = None,
        qr: bool = False,
    ) -> None:
        """
        sync userbot process
        for logo, logger and start async

        Args:
            web (bool): Login with webUI or not
            token (str): Inline bot token
            qr (bool): Login via QR code
        """

        print(logo)
        logger.load(self.levels.get(level.lower()))

        try:
            self.loop.run_until_complete(self.amain(web, token, qr))
        except KeyboardInterrupt:
            print("stopping...")


userbot = Userbot()
