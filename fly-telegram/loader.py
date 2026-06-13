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
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Union

from pyrogram import Client, filters
from pyrogram.handlers import EditedMessageHandler, MessageHandler
from pyrogram.types import Message

try:
    import ujson as json  # noqa: F401
except ModuleNotFoundError:
    pass

THE_DIR = Path(__file__).parent
if str(THE_DIR) not in sys.path:
    sys.path.append(str(THE_DIR))

from database import database  # noqa: E402


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
        """
        The wrapper object

        Args:
            client (pyrogram.Client): pyrogram client object
            func (Callable/Any): The function
        """
        self.client: Client = client
        self.func: Callable[..., Any] = func
        self.filters: Any = filters
        self.message: Optional[Message] = None
        self.command: Optional[str] = None
        self.args: list[str] = []

        self.timeout: int = getattr(func, 'timeout', 30)
        self.no_timeout: bool = getattr(func, 'no_timeout', False)

    async def __call__(self, message: Message) -> None:
        """
        The call object.

        Args:
            message (pyrogram.types.Message): pyrogram message object
        """
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
        """
        process the message
        """
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
        self.loops: dict[str, list[tuple[Callable, int]]] = {}

    @staticmethod
    def on_load(func: Callable) -> Callable:
        """
        If module is loaded decorator

        Args:
            func (Callable): The function
        """
        func.on_load = True
        return func

    @staticmethod
    def loop(every: int) -> Callable:
        """
        Loop the function decorator

        Args:
            func (Callable): The function
        """
        def decorator(func: Callable) -> Callable:
            func.loop = True
            func.loop_interval = every
            return func
        return decorator

    @staticmethod
    def watcher(type: str = "message", regex: str = None,
                out: bool = False, coming: bool = True):
        """
        Message watcher decorator

        Args:
            type (str): The type
            regex (str): The regex optinal
            out (bool): Is out message?
            coming (bool): Its coming message
        """
        def decorator(func: Callable) -> Callable:
            func.watcher = True
            func.watcher_type = type
            func.watcher_regex = regex
            func.watcher_out = out
            func.watcher_coming = coming
            return func
        return decorator


events = Events()


class ValidationError(Exception):
    pass


class Validator:
    def __init__(self, err: str = "Invalid value"):
        self.err = err

    def validate(self, value: Any) -> Any:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


class String(Validator):
    def __init__(self, min: int = 0, max: int = 4096, err: str = "Must be a string"):
        super().__init__(err)
        self.min = min
        self.max = max

    def validate(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValidationError(self.err)
        if len(value) < self.min:
            raise ValidationError(f"string too short (min {self.min})")
        if len(value) > self.max:
            raise ValidationError(f"string too long (max {self.max})")
        return value


class Link(Validator):
    def __init__(self, err: str = "Must be a link"):
        super().__init__(err)

    def validate(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValidationError(self.err)
        pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        if not pattern.match(value):
            raise ValidationError(self.err)
        return value


class Integer(Validator):
    def __init__(self, min: Optional[int] = None, max: Optional[int] = None,
                 err: str = "Must be an int"):
        super().__init__(err)
        self.min = min
        self.max = max

    def validate(self, value: Any) -> int:
        try:
            val = int(value)
        except (ValueError, TypeError):
            raise ValidationError(self.err)
        if self.min is not None and val < self.min:
            raise ValidationError(f"Value must be >= {self.min}")
        if self.max is not None and val > self.max:
            raise ValidationError(f"Value must be <= {self.max}")
        return val


class Boolean(Validator):
    def __init__(self, err: str = "Must be a bool (True/False)"):
        super().__init__(err)

    def validate(self, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ("true", "1", "yes", "on"):
                return True
            if value.lower() in ("false", "0", "no", "off"):
                return False
        raise ValidationError(self.err)


class Float(Validator):
    def __init__(self, min: Optional[float] = None, max: Optional[float] = None,
                 err: str = "Must be a float"):
        super().__init__(err)
        self.min = min
        self.max = max

    def validate(self, value: Any) -> float:
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValidationError(self.err)
        if self.min is not None and val < self.min:
            raise ValidationError(f"Value must be >= {self.min}")
        if self.max is not None and val > self.max:
            raise ValidationError(f"Value must be <= {self.max}")
        return val


class Choice(Validator):
    def __init__(self, choices: list, err: str = "Invalid choice"):
        super().__init__(err)
        self.choices = choices

    def validate(self, value: Any) -> Any:
        if value not in self.choices:
            raise ValidationError(
                f"{self.err}. Allowed: {', '.join(str(c) for c in self.choices)}"
            )
        return value


class ConfigValue:
    __slots__ = ("name", "default", "doc", "validator", "on_change", "_owner")

    def __init__(
        self,
        name: str,
        default: Any,
        doc: Union[str, Callable[[], str]] = "",
        validator: Optional[Validator] = None,
        on_change: Optional[Callable] = None,
    ):
        self.name = name
        self.default = default
        self.doc = doc if isinstance(doc, str) else doc()
        self.validator = validator
        self.on_change = on_change
        self._owner: Optional[str] = None

    def validate(self, value: Any) -> Any:
        if self.validator:
            return self.validator.validate(value)
        return value

    def __repr__(self) -> str:
        return (
            f"ConfigValue(name={self.name!r}, default={self.default!r}, "
            f"validator={self.validator!r})"
        )


class ModuleConfig:
    def __init__(self, *values: ConfigValue):
        self.values: dict[str, ConfigValue] = {}
        self.name: Optional[str] = None
        self.key: str = "config"
        self.cache: dict[str, Any] = {}

        for v in values:
            self.values[v.name] = v

    def _set_module(self, name: str) -> None:
        self.name = name
        self._db()

    def _db(self) -> None:
        data = database.get(self.key, self.name) or {}
        self.cache = {}

        for name, cfg_value in self.values.items():
            if name in data:
                self.cache[name] = data[name]
            else:
                self.cache[name] = cfg_value.default

        configs = database.get(self.key)
        if not isinstance(configs, dict):
            configs = {}
        configs[self.name] = self.cache
        database.set(self.key, configs)

    def _save(self) -> None:
        all_cfg = database.get(self.key)
        if not isinstance(all_cfg, dict):
            all_cfg = {}
        all_cfg[self.name] = self.cache
        database.set(self.key, all_cfg)

    def __getitem__(self, key: str) -> Any:
        if key not in self.values:
            raise KeyError(
                f"Config key '{key}' not defined for module '{self.name}'")
        return self.cache.get(key, self.values[key].default)

    def __setitem__(self, key: str, value: Any) -> None:
        if key not in self.values:
            raise KeyError(
                f"Config key '{key}' not defined for module '{self.name}'")

        cfg_value = self.values[key]
        valid = cfg_value.validate(value)
        old_value = self.cache.get(key)
        self.cache[key] = valid
        self._save()

        if cfg_value.on_change and old_value != valid:
            if callable(cfg_value.on_change):
                cfg_value.on_change(old_value, valid)

    def __getattr__(self, key: str) -> Any:
        if key.startswith("_") or key in ("values", "name", "key", "cache"):
            return object.__getattribute__(self, key)
        if key in self.values:
            return self[key]
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{key}'")

    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith("_") or key in ("values", "name", "key", "cache"):
            object.__setattr__(self, key, value)
        else:
            self[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.values

    def __iter__(self):
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def __repr__(self) -> str:
        items = ", ".join(
            f"{k}={self.cache.get(k, v.default)!r}"
            for k, v in self.values.items()
        )
        return f"ModuleConfig({items})"

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def set(self, key: str, value: Any) -> None:
        self[key] = value

    def items(self):
        for name in self.values:
            yield name, self.cache.get(name, self.values[name].default)

    def keys(self):
        return self.values.keys()

    def values(self):
        for name in self.values:
            yield self.cache.get(name, self.values[name].default)

    def reset(self, key: str) -> None:
        if key not in self.values:
            raise KeyError(f"Config key '{key}' not defined")
        self[key] = self.values[key].default

    def resetall(self) -> None:
        for name, cfg_value in self.values.items():
            self.cache[name] = cfg_value.default
        self._save()


class _Validators:
    String = String
    Link = Link
    Integer = Integer
    Boolean = Boolean
    Float = Float
    Choice = Choice
    Validator = Validator


validators = _Validators()


class Loader:
    """fly-telegram modules loader"""

    def __init__(self) -> None:
        self.modules_path: Path = (
            Path(f"./{__package__}/modules") if __package__
            else Path("./fly-telegram/modules")
        )  # if not package - many path

        self.core_modules: tuple[str, ...] = (
            "help", "loader",
            "core", "executor",
            "configurator", "chats",
        )
        self.command_handlers: dict[str, list[MessageHandler]] = {}
        self.func_events: dict[str, dict[str, list[Callable]]] = {}
        self.func_tasks: dict[str, list[asyncio.Task]] = {}
        self._package_prefix: str = (
            f"{__package__}.modules." if __package__
            else "fly-telegram.modules."
        )  # if not package - many path
        self.events = events
        self.ModuleConfig = ModuleConfig
        self.ConfigValue = ConfigValue
        self.validators = validators

    @staticmethod
    def alias(*aliases: str) -> Callable:
        """
        The aliases decorator

        Args:
            *aliases (str): The aliases list
        """
        def decorator(func: Callable) -> Callable:
            func.aliases = aliases
            return func
        return decorator

    @staticmethod
    def timeout(seconds: int) -> Callable:
        """
        Set timeout manyally for command decorator

        Args:
            seconds (int): The time
        """
        def decorator(func: Callable) -> Callable:
            func.timeout = seconds
            return func
        return decorator

    @staticmethod
    def no_timeout(func: Callable) -> Callable:
        """
        Disable timeout error for the command decorator
        """
        func.no_timeout = True
        return func

    async def load(self, name: str, client: Client, startup: bool = False) -> bool:
        """
        Load the module by name

        Args:
            name (str): module name
            client (pyrogram.Client): the pyrogram client object
            startup (bool): The module load on userbot startup?

        Returns:
            bool: Its module loaded?
        """
        path: Path = self.modules_path / name

        if not path.exists():
            raise ModuleNotFoundError(f"Module '{name}' not found!")

        if name in self.command_handlers:
            await self.unload(name, client)

        self.func_events[name] = {
            "load": [],
            "watchers": [],
            "loops": []
        }

        self.func_tasks[name] = []

        sources: Path = path / "src"
        module_commands: list[str] = []
        module_prefix: str = f"{self._package_prefix}{name}.src."

        for file in sources.glob('*.py'):
            module_name: str = f"{module_prefix}{file.stem}"
            try:
                module: Any = self._import_or_reload(module_name)
            except Exception as e:
                raise ModuleImportError(
                    f"Failed to import module {module_name}: {e}"
                ) from e

            # Bind ModuleConfig instances to the module
            for attr_name, attr_val in vars(module).items():
                if isinstance(attr_val, ModuleConfig):
                    attr_val._set_module(name)

            for func_name, func in inspect.getmembers(module, inspect.isfunction):
                if func_name.endswith("_cmd"):
                    aliases = getattr(func, 'aliases', ())
                    command_name: str = func_name[:-4]
                    names = {command_name}.union(aliases)

                    for command in names:
                        module_commands.append(command)
                        self._register_command(client, command, func, name)

                if getattr(func, "on_load", False):
                    self.func_events[name]["load"].append(func)
                if getattr(func, "watcher", None):
                    self._register_watcher(client, func, name)
                if getattr(func, "loop", False):
                    every = getattr(func, "loop_interval", 60)
                    self.func_events[name]["loops"].append((func, every))

                    task = asyncio.create_task(
                        self._run_loop(client, func, every, name)
                    )
                    self.func_tasks[name].append(task)

            for event in self.func_events[name]["load"]:
                if inspect.iscoroutinefunction(event):
                    asyncio.create_task(event(client))
                else:
                    event(client)

            self._process_module_handlers(module, client)

        if not startup:
            await self._restart_dispatcher(client)

        return True

    async def _run_loop(self, client: Client, func: Callable,
                        every: int, name: str) -> None:
        """
        Run loop for the command

        Args:
            client (pyrogram.Client): The pyrogram client object
            func (Callable): The function
            every (int): Every command executed by seconds
            name (str): Module name
        """
        while True:
            try:
                if inspect.iscoroutinefunction(func):
                    await func(client)
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        None, func, client)

                await asyncio.sleep(every)
            except asyncio.CancelledError:
                break

            except Exception as error:
                logging.error(f"Module '{name}' loop error: {error}")

    def _register_watcher(self, client: Client,
                          func: Callable, name: str) -> MessageHandler:
        """
        Register module watcher

        Args:
            client (pyorgram.Client): The pyrogram client object
            func (Callable): The function
            name (str): The module name

        Returns:
            pyrogram.types.MessageHandler: The message object
        """

        watcher_type: str = getattr(func, "watcher_type", "message")
        watcher_regex: str = getattr(func, "watcher_regex", None)

        watcher_out: bool = getattr(func, "watcher_out", False)
        watcher_coming: bool = getattr(func, "watcher_coming", True)

        # ia tochno peredelayi ne pod filtri. ili tak norm?

        watcher_types: dict[str, Any] = {  # maybe shitcode. sorry
            "all": filters.all,
            "message": filters.text,
            "photo": filters.photo,
            "video": filters.video,
            "voice": filters.voice,
            "audio": filters.audio,
            "document": filters.document,
            "sticker": filters.sticker,
        }

        used = watcher_types.get(watcher_type)

        if watcher_out and not watcher_coming:
            used &= filters.me
        elif watcher_coming and not watcher_out:
            used &= ~filters.me

        if watcher_regex:
            used &= filters.regex(watcher_regex)

        async def wrapper(c: Client, message: Message):
            try:
                if inspect.iscoroutinefunction(func):
                    await func(c, message)
                else:
                    func(c, message)
            except Exception as err:
                logging.error(f"watcher error in {name}: {err}")

        handler = MessageHandler(wrapper, filters=used)
        client.add_handler(handler)
        self.command_handlers.setdefault(name, []).append(handler)

        return handler

    def _import_or_reload(self, module_name: str) -> Any:
        """
        Import module or reload
        Args:
            module_name (str): The module name
        """
        if module_name in sys.modules:
            return importlib.reload(sys.modules[module_name])
        return importlib.import_module(module_name)

    def _process_module_handlers(self, module: Any, client: Client) -> None:
        """
        Register handlers from module
        Args:
            module (Any): The module object
            client (pyrogram.Client): The pyrogram client object
        """
        for obj in vars(module).values():
            handlers: list[tuple[Any, int]] = getattr(obj, "handlers", [])
            if isinstance(handlers, list):
                for handler, group in handlers:
                    client.add_handler(handler, group)

    async def _restart_dispatcher(self, client: Client) -> None:
        """
        Restart the dispatcher!
        Args:
            client (pyrogram.Client): The pyrogram client object
        """
        await client.dispatcher.stop(clear_handlers=False)
        await client.dispatcher.start()

    def _register_command(self, client: Client, command_name: str,
                          func: Callable[..., Any], module_name: str) -> None:
        """
        Register the command
        Args:
            client (pyrogram.Client): The pyerogram client object
            command_name (str): The command name
            func (Callable/Any): The function
            module_name (str): The module name
        """
        wrapper: CommandWrapper = CommandWrapper(client, func)

        async def wrapped_command(_: Any, message: Message) -> None:
            await wrapper(message)

        cmd_filter = filters.command([command_name], ".") & filters.me

        handler: MessageHandler = MessageHandler(
            wrapped_command,
            cmd_filter
        )
        client.add_handler(handler)

        edited_handler: EditedMessageHandler = EditedMessageHandler(
            wrapped_command,
            cmd_filter
        )
        client.add_handler(edited_handler)

        handlers_list: list[MessageHandler] = self.command_handlers.setdefault(
            module_name, [])
        handlers_list.append(handler)
        handlers_list.append(edited_handler)

    async def unload(self, name: str, client: Client) -> bool:
        """
        Unload module by name

        Args:
            name (str): The module name
            client (pyrogram.Client): The pyrogram client object

        Returns:
            bool: Module unloaded?
        """
        if name in self.core_modules:
            raise PermissionError("Cannot unload core module!")

        if name in self.func_tasks:
            for task in self.func_tasks[name]:
                task.cancel()
            if self.func_tasks[name]:
                await asyncio.gather(*self.func_tasks[name], return_exceptions=True)
            del self.func_tasks[name]

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
        """
        Load all modules from directory
        Args:
            client (pyrogram.Client): The pyrogram client object
        """
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
