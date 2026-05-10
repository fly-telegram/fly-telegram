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

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .loader import Loader


class ModuleHandler(FileSystemEventHandler):
    def __init__(self, reload_callback, loop, modules_path):
        """
        Handler for module reloading
        Args:
            reload_callback (Callable): The callback for module reloading
            loop (asyncio.get_event_loop): The current loop
            modules_path (pathlib.Path): The dir path
        """
        self.callback = reload_callback
        self.modules_path = modules_path
        self.loop = loop

    def on_modified(self, event):
        """
        on moodified file
        Args:
            event: The event
        """
        if not event.is_directory and event.src_path.endswith(".py"):
            mod_path = Path(event.src_path)
            if mod_path.parent.name != "__pycache__":
                rel_path = mod_path.relative_to(self.modules_path)
                parts = rel_path.parts

                mod_file = mod_path.name
                mod_name = parts[0]

                asyncio.run_coroutine_threadsafe(
                    self.callback(mod_name),
                    self.loop
                )

                logging.info(
                    f"Module '{mod_name}' file '{mod_file}' was modified.")


class FilesWatcher:
    def __init__(self, client):
        self.client = client
        self.loader = Loader()
        self.observer = None
        self.loop = asyncio.get_event_loop()

    async def watch(self):
        """
        Load the FilesWatcher
        """
        path = Path(f"{__package__}/modules")
        logging.info("FilesWatcher is loaded.")

        handler = ModuleHandler(self.reload, self.loop, path)

        self.observer = Observer()
        self.observer.schedule(handler, str(path), recursive=True)
        self.observer.start()

    async def stop(self):
        """
        Stop the fileswatcher
        """
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logging.info("FilesWatcher stopped.")

    async def reload(self, mod_name: str):
        """
        Reload the module by name
        Args:
            mod_name (str): The module
        """
        try:
            logging.info(f"Reloading module '{mod_name}'...")
            await self.loader.unload(mod_name, self.client)
            await self.loader.load(mod_name, self.client)
        except Exception as err:
            logging.error(f"Failed to reload module '{mod_name}': {err}")
