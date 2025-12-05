#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#               Licensed under the -by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import logging
import sys
import uvicorn

from pyrogram import idle

from .auth import Auth
from .inline import inline
from .loader import Loader
from .utils import logo
from . import logger

try:
    import uvloop

    uvloop.install()
except Exception:
    pass


class Userbot:
    def __init__(self):
        self.loader = Loader()
        self.auth = Auth()
        self.loop = asyncio.get_event_loop()

        self.levels = {
            "info": logging.INFO,
            "debug": logging.DEBUG,
            "error": logging.ERROR,
            "warning": logging.WARNING
        }

    async def amain(self):
        """
        async userbot process
        for setting client, loader and etc.
        """
        client, me = await self.auth.load(web=False)

        await client.initialize()
        await client.dispatcher.start()

        logging.info(f"Started on the {me.first_name}")

        if not client.me:
            client.me = me

        await inline.start()

        await self.loader.load_all(client)

        await idle()
        return True

    def main(self, level: str = "info"):
        """
        sync userbot process
        for logo, logger and start async
        """

        print(logo)
        logger.load(self.levels.get(level))

        try:
            self.loop.run_until_complete(self.amain())
        except KeyboardInterrupt:
            print("stopping...")


userbot = Userbot()

if __name__ == "__main__":
    userbot.main()
