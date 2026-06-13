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
import os

from logging.handlers import RotatingFileHandler
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .database import database
from .utils import BASE_DIR
from pyrogram import Client


class InlineHandler(logging.StreamHandler):
    def __init__(self, client: Client):
        """Inline bot logging handler"""
        super().__init__()
        self.client: Client = client
        self._buffer: list[str] = []
        self._lock = asyncio.Lock()
        self._max = 3500
        try:
            self._task: asyncio.Task = asyncio.ensure_future(self._loop())
        except Exception:
            self._task = None

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < logging.WARNING:
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._put(record))
        except Exception:
            pass

    async def _put(self, record: logging.LogRecord) -> None:
        log_entry = self.format(record)
        async with self._lock:
            self._buffer.append(log_entry)

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(5)
            await self.main()

    async def main(self) -> None:
        async with self._lock:
            if not self._buffer:
                return
            entries = self._buffer[:]
            self._buffer.clear()

        try:
            text = "\n".join(entries)
            if len(text) > self._max:
                text = text[:self._max] + "\n..."
            chats = database.get("chats")
            if not isinstance(chats, dict):
                return
            logID = chats.get("logs")
            if not logID:
                return
            if (
                    hasattr(self.client, "inline")
                    and self.client.inline
                    and self.client.inline.bot):
                await self.client.inline.bot.send_message(
                    logID,
                    f"<code>{text}</code>",
                    parse_mode="html",
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[[
                            InlineKeyboardButton(
                                text="⚠️ Issues",
                                url="https://github.com/fly-telegram/fly-telegram/issues",
                            )
                        ]]
                    ),
                )
        except Exception:
            pass

    def close(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
        super().close()


class FilesHandler(logging.Handler):
    def __init__(self, dir: str, formatter: logging.Formatter):
        super().__init__()
        self._dir = dir
        self._formatter = formatter
        os.makedirs(dir, exist_ok=True)
        self._handlers = self._setup_handlers()

    def _setup_handlers(self) -> dict[int, RotatingFileHandler]:
        mapping = {
            logging.DEBUG: "debug.log",
            logging.INFO: "info.log",
            logging.WARNING: "warning.log",
            logging.ERROR: "errors.log",
        }
        handlers = {}
        for level, filename in mapping.items():
            handler = RotatingFileHandler(
                os.path.join(self._dir, filename),
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
            handler.setLevel(level)
            handler.setFormatter(self._formatter)
            handlers[level] = handler
        return handlers

    def emit(self, record: logging.LogRecord) -> None:
        for level, handler in self._handlers.items():
            if record.levelno >= level:
                handler.emit(record)

    def close(self) -> None:
        for handler in self._handlers.values():
            handler.close()
        super().close()


def load(level: logging.NOTSET) -> logging.Logger:  # type: ignore
    """
    Load the logging proc

    Args:
        level (logging.NOTSET): The log level object

    Returns:
        logging.Logger: logger object
    """
    logger_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(funcName)s: %(lineno)d - %(message)s",
        "%m-%d %H:%M:%S")

    logger = logging.getLogger()
    logger.handlers = []
    logger.setLevel(level)

    console = logging.StreamHandler()
    console.setFormatter(logger_format)
    logger.addHandler(console)

    fileshandler = FilesHandler(os.path.join(BASE_DIR, "logs"), logger_format)
    logger.addHandler(fileshandler)

    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

    return logger
