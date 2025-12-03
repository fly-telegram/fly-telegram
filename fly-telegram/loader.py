#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import importlib
import inspect
import logging
import sys
from pathlib import Path

from telethon import TelegramClient

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

THE_DIR = Path(__file__).parent
if str(THE_DIR) not in sys.path:
    sys.path.append(str(THE_DIR))

modules = {}


class CommandWrapper:
    def __init__(self, client: Client, tl_client: TelegramClient, func):
        self.client = client
        self.tl_client = tl_client

        self.func = func
        self.filters = filters
        self.message = None
        self.command = None
        self.args = []

    async def __call__(self, message: Message):
        self.message = message
        self.command = message.command[0]
        self.args = message.command[1:]

        arguments = inspect.getfullargspec(self.func).args
        arguments.remove('self')

        if len(self.args) < len(arguments):
            await message.edit("❌ <b>Command arguments required! {}</b>".format(
                ", ".join(arguments)))
        else:
            try:
                await self.func(self, *self.args)
            except Exception as e:
                await message.edit(f"❌ <b>Error: {e}</b>")

    def __getattr__(self, name):
        return getattr(self.client, name)


class Loader:
    """fly-telegram modules loader"""

    def __init__(self):
        self.modules_path = Path(f"./{__package__}/modules")
        self.core_modules = ("help", "loader", "core", "executor")
        self.command_handlers = {}

    async def load(self, name: str, client: Client, tl_client: TelegramClient) -> bool:
        path = self.modules_path / name

        if not path.exists():
            raise ValueError(f"Module '{name}' not found!")

        if name in self.command_handlers:
            await self.unload(name, client)

        sources = path / "src"
        module_commands = []

        # importing all files
        for file in sources.glob('*.py'):
            module_name = f"{__package__}.modules.{name}.src.{file.stem}"
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)

            for func_name, func in inspect.getmembers(module, inspect.isfunction):
                if func_name.endswith("_cmd"):
                    command_name = func_name[:-4]

                    module_commands.append(command_name)

                    self._register_command(
                        client, tl_client, command_name, func, name)

            for obj_name, obj in vars(module).items():
                handlers = getattr(obj, "handlers", [])
                if not isinstance(handlers, list):
                    continue

                for handler, group in handlers:
                    client.add_handler(handler, group)

        modules[name] = module_commands

        # restart dispatcher.
        await client.dispatcher.stop()
        await client.dispatcher.start()

        return True

    def _register_command(self, client: Client, tl_client: TelegramClient, command_name: str, func, module_name: str):
        wrapper = CommandWrapper(client, tl_client, func)

        async def wrapped_command(_, message: Message):
            await wrapper(message)

        commands = [command_name]

        handler = MessageHandler(
            wrapped_command,
            filters.command(commands, ".") & filters.me
        )
        client.add_handler(handler)

        if module_name not in self.command_handlers:
            self.command_handlers[module_name] = []
        self.command_handlers[module_name].append(handler)

    async def unload(self, name: str, client: Client, tl_client: TelegramClient) -> bool:
        if name not in self.command_handlers:
            return False

        for handler in self.command_handlers[name]:
            client.remove_handler(handler)

        del self.command_handlers[name]

        for module in list(sys.modules):
            if module.startswith(f"{__package__}.modules.{name}."):
                del sys.modules[module]

        return True

    async def load_all(self, client: Client, tl_client: TelegramClient) -> None:
        for module in self.modules_path.iterdir():
            if module.is_dir() and not module.name.endswith("_"):
                try:
                    await self.load(module.name, client, tl_client)
                except Exception as error:
                    logging.error(
                        f"Error loading module '{module.name}': {error}")
