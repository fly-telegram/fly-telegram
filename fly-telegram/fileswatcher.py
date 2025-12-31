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
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from .loader import Loader

class ModuleHandler(FileSystemEventHandler):
    def __init__(self, reload_callback, loop):
        self.callback = reload_callback
        self.loop = loop

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswitch(".py"):
            mod_path = Path(event.src_path)
            if mod_path.parent.name != "__pycache__":
                mod_name = mod_path.parent.name
                mod_file = mod_path.name

                asyncio.run_coroutine_threadsafe(
                    self.callback(mod_name),
                    self.loop
                )

                logging.info(f"Module '{mod_name}' file '{mod_file}' was modified.")

class FilesWatcher:
    def __init__(self, client):
        self.client = client
        self.loader = Loader()
        self.observer = None
        self.loop = asyncio.get_event_loop()

    async def watch(self):
        path = Path(f"{__package__}/modules")
        logging.info("FilesWatcher is loaded.")

        handler = ModuleHandler(self.reload, self.loop)

        self.observer = Observer()
        self.observer.schedule(handler, str(path), recursive=True)

    async def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logging.info("FilesWatcher stopped.")

    async def reload(self, mod_name: str):
        try:
            logging.info(f"Reloading module '{mod_name}'...")
            await self.loader.unload(mod_name, self.client)
            await self.loader.load(mod_name, self.client)
        except Exception as err:
            logging.error(f"Failed to reload module '{mod_name}'.")