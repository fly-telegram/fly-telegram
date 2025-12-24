#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import logging
from pathlib import Path

from watchfiles import awatch

from .loader import Loader


class FilesWatcher:
    def __init__(self, client):
        self.client = client
        self.loader = Loader()

    async def watch(self):
        path = Path(f"./{__package__}/modules")
        logging.info("FilesWatcher is loaded.")

        try:
            async for changes in awatch(path):
                tasks = []
                for change in changes:
                    if change[1].endswith(".py"):
                        module_name = Path(change[1]).parent.parent.name
                        file_name = Path(change[1]).name

                        tasks.append(self.reload(module_name))
                        logging.info(
                            f"Module '{module_name}' file '{file_name}' was modified.")

                await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logging.info("FilesWatcher stopped.")

    async def reload(self, module_name):
        print(f"Reloading module {module_name}")
        await self.loader.unload(module_name, self.client)
        print(f"Unloaded module {module_name}")
        await self.loader.load(module_name, self.client)
        print(f"Loaded module {module_name}")


async def load(client):
    watcher = FilesWatcher(client)
    await watcher.watch()
