#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import importlib
import inspect
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

if TYPE_CHECKING:
    pass

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

THE_DIR = Path(__file__).parent
if str(THE_DIR) not in sys.path:
    sys.path.append(str(THE_DIR))


class LoaderError(Exception):
    pass


class ModuleNotFoundError(LoaderError):
    pass


class ArgumentsError(LoaderError):
    pass


class ModuleImportError(LoaderError):
    pass


class CommandWrapper:
    __slots__ = ('client', 'func', 'filters', 'message',
                 'command', 'args', 'no_timeout', 'timeout')

    def __init__(self, client: Client, func: Callable[..., Any]) -> None:
        self.client: Client = client
        self.func: Callable[..., Any] = func
        self.filters: Any = filters
        self.message: Optional[Message] = None
        self.command: Optional[str] = None
        self.args: list[str] = []

        self.timeout: int = getattr(func, 'timeout', 30)
        self.no_timeout: bool = getattr(func, 'no_timeout', False)

    async def __call__(self, message: Message) -> None:
        self.message = message
        self.command = message.command[0] if message.command else ""

        full = message.text.strip() if message.text else ""
        if full.startswith(f".{self.command}"):
            args_text = full[len(self.command) + 1:].lstrip()
            self.args = args_text.split() if args_text else []
        else:
            self.args = []

        command_task = asyncio.create_task(self._process_command())

        try:
            if not self.no_timeout:
                await asyncio.wait_for(command_task, timeout=self.timeout)
            else:
                await command_task
        except asyncio.CancelledError:
            await self.message.edit("❌ <b>Command Cancelled</b>")
        except asyncio.TimeoutError:
            await self.message.edit("❌ <b>Command TimeOut error</b>")
        except ArgumentsError as e:
            await self.message.edit(f"❌ <b>Arguments Error: {e}</b>")
        except Exception as e:
            await self.message.edit(f"❌ <b>Error: {e}</b>")

    async def _process_command(self) -> None:
        arguments = inspect.getfullargspec(self.func).args
        exp_args = [arg for arg in arguments if arg != 'self']

        if not exp_args:
            return await self.func(self)

        full = self.message.text.strip() if self.message.text else ""
        if full.startswith(f".{self.command}"):
            text = full[len(self.command) + 1:].lstrip()
        else:
            text = ""

        if len(exp_args) == 1:
            return await self.func(self, text)

        splitted = text.split(maxsplit=len(exp_args) - 1)

        if len(splitted) < len(exp_args) - 1:
            missing = ", ".join(exp_args[len(splitted):])
            raise ArgumentsError(f"Required arguments: {missing}")

        args = splitted[:len(exp_args) - 1]

        if len(splitted) == len(exp_args) - 1:
            last = ""
        elif len(splitted) == len(exp_args):
            args.append(splitted[-1])
            return await self.func(self, *args)
        else:
            start = len(' '.join(args)) + 1 if args else 0
            last = text[start:].strip()
            args.append(last)

        await self.func(self, *args)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.client, name)


class Events:
    def __init__(self) -> None:
        self.load: dict[str, list[Callable]] = {}
        self.watchers: dict[str, list[Callable]] = {}

    @staticmethod
    def on_load(func: Callable) -> Callable:
        func.on_load = True
        return func

    @staticmethod
    def watcher(func: Callable) -> Callable:
        func.watcher = True
        return func


events = Events()


class Loader:
    """fly-telegram modules loader"""

    def __init__(self) -> None:
        self.modules_path: Path = (
            Path(f"./{__package__}/modules") if __package__
            else Path("./fly-telegram/modules")
        )  # if not package - many path

        self.core_modules: tuple[str, ...] = (
            "help", "loader", "core", "executor")
        self.command_handlers: dict[str, list[MessageHandler]] = {}
        self.func_events: dict[str, dict[str, list[Callable]]] = {}
        self._package_prefix: str = (
            f"{__package__}.modules." if __package__
            else "fly-telegram.modules."
        )  # if not package - many path
        self.events = events

    @staticmethod
    def timeout(seconds: int) -> Callable:
        def decorator(func: Callable) -> Callable:
            func.timeout = seconds
            return func
        return decorator

    @staticmethod
    def no_timeout(func: Callable) -> Callable:
        func.no_timeout = True
        return func

    async def load(self, name: str, client: Client, startup: bool = False) -> bool:
        """load module by name"""
        path: Path = self.modules_path / name

        if not path.exists():
            raise ModuleNotFoundError(f"Module '{name}' not found!")

        if name in self.command_handlers:
            await self.unload(name, client)

        self.func_events[name] = {
            "load": [],
            "watchers": []
        }

        sources: Path = path / "src"
        module_commands: list[str] = []
        module_prefix: str = f"{self._package_prefix}{name}.src."

        for file in sources.glob('*.py'):
            module_name: str = f"{module_prefix}{file.stem}"
            try:
                module: Any = self._import_or_reload(module_name)
            except Exception as e:
                raise ModuleImportError(
                    f"Failed to import module {module_name}: {e}")

            for func_name, func in inspect.getmembers(module, inspect.isfunction):
                if func_name.endswith("_cmd"):
                    command_name: str = func_name[:-4]
                    module_commands.append(command_name)
                    self._register_command(client, command_name, func, name)
                if getattr(func, "on_load", False):
                    self.func_events[name]["load"].append(func)
                # if getattr(func, "watcher"):
                #    self._register_watcher(client, func, name)

            for event in self.func_events[name]["load"]:
                if inspect.iscoroutinefunction(event):
                    asyncio.create_task(event(client))
                else:
                    event(client)

            self._process_module_handlers(module, client)

        if not startup:
            await self._restart_dispatcher(client)

        return True

    def _import_or_reload(self, module_name: str) -> Any:
        if module_name in sys.modules:
            return importlib.reload(sys.modules[module_name])
        return importlib.import_module(module_name)

    def _process_module_handlers(self, module: Any, client: Client) -> None:
        """register handlers from module"""
        for obj in vars(module).values():
            handlers: list[tuple[Any, int]] = getattr(obj, "handlers", [])
            if isinstance(handlers, list):
                for handler, group in handlers:
                    client.add_handler(handler, group)

    async def _restart_dispatcher(self, client: Client) -> None:
        await client.dispatcher.stop(clear_handlers=False)
        await client.dispatcher.start()

    def _register_command(self, client: Client, command_name: str,
                          func: Callable[..., Any], module_name: str) -> None:
        """register command"""
        wrapper: CommandWrapper = CommandWrapper(client, func)

        async def wrapped_command(_: Any, message: Message) -> None:
            await wrapper(message)

        handler: MessageHandler = MessageHandler(
            wrapped_command,
            filters.command([command_name], ".") & filters.me
        )
        client.add_handler(handler)

        handlers_list: list[MessageHandler] = self.command_handlers.setdefault(
            module_name, [])
        handlers_list.append(handler)

    async def unload(self, name: str, client: Client) -> bool:
        """unload module by name"""
        if name not in self.command_handlers:
            return False

        handlers: list[MessageHandler] = self.command_handlers[name]
        for handler in handlers:
            client.remove_handler(handler)

        del self.command_handlers[name]

        prefix: str = f"{self._package_prefix}{name}."
        modules_to_delete: list[str] = [
            module for module in sys.modules.keys()
            if module.startswith(prefix)
        ]

        for module in modules_to_delete:
            del sys.modules[module]

        return True

    async def load_all(self, client: Client) -> None:
        """load all modules"""
        modules_to_load: list[Path] = [
            module for module in self.modules_path.iterdir()
            if module.is_dir() and not module.name.endswith("_")
        ]

        for module in modules_to_load:
            try:
                await self.load(module.name, client, startup=True)
            except ModuleImportError as error:
                logging.error(
                    f"Import error in module '{module.name}': {error}")
            except ModuleNotFoundError as error:
                logging.error(f"Module '{module.name}' not found: {error}")
            except Exception as error:
                logging.error(
                    f"Unexpected error loading module '{module.name}': {error}")

        await self._restart_dispatcher(client)
