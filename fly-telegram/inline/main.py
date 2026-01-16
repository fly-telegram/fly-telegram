#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from typing import Union, Optional, List, Dict, Any, Callable
from uuid import uuid4

from aiogram import Bot, Dispatcher, types
from aiogram.utils.exceptions import Unauthorized
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from pyrogram import Client

from .call import InlineCall
from .botmanager import BotManager
from database import database

class Via:
    def __init__(self) -> None:
        self.active: Dict[str, Dict[str, Any]] = {}
        self.results: Dict[str, types.InlineQueryResult] = {}

    def add(
        self,
        text: str,
        buttons: Optional[List[List[Dict]]] = None,
        descripton: str = "Fly-Telegram system result.",
    ):
        query_id = str(uuid4())
        input_text = InputTextMessageContent(
            message_text=text,
        )

        reply_markup = []
        if buttons:
            keyboard = []

            for brow in buttons:
                row = []
                for btn in brow:
                    row.append(
                        InlineKeyboardButton(
                            text=btn.get("text", "button"),
                            callback_data=btn.get("callback", f"via_{query_id}_{len(keyboard)}")
                        )
                    )
                keyboard.append(row)
            reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)

        result = InlineQueryResultArticle(
            id=f"via_{query_id}",
            title="🕊️ fly telegram v2",
            descripton=descripton,
            input_message_content=input_text,
            reply_markup=reply_markup
        )

        self.active[query_id] = {
            "text": text,
            "reply_markup": buttons,
        }

        self.results[query_id] = result

        return query_id
    
    def get_result(self, id: str):
        return self.results[id]
    
    def update(self, id: str, **kwargs):
        if id in self.active:
            self.active[id].update(kwargs)
            if id in self.results:
                result = self.results[id]
                if "text" in kwargs:
                    result.input_message_content.message_text = kwargs["text"]
                if "buttons" in kwargs:
                    if kwargs["buttons"]:
                        keyboard = []
                        for brow in kwargs["buttons"]:
                            row = []
                            for btn in brow:
                                row.append(
                                    InlineKeyboardButton(
                                        text=btn.get("text", "button"),
                                        callback_data=btn.get("callback", f"via_{id}_{len(keyboard)}")
                                    )
                                )
                                keyboard.append(row)
                        result.reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
                    else:
                        result.reply_markup = None


class Inline:
    def __init__(self):
        self._bot = None
        self.dp = None
        self.viamanager = Via()
        logging.debug("New instance: %s", id(self))

        # suka, takoi govnokod nize, no ia zaebalsa. kto pofixit eto - pull request pls. ia ne znay chto delat....
        if '_inline' not in sys.modules:
            sys.modules['_inline'] = {'handlers': {}}
        elif 'handlers' not in sys.modules['_inline']:
            sys.modules['_inline']['handlers'] = {}

        self.handlers = sys.modules['_inline']['handlers']

    def via(
        self,
        text: str,
        buttons = None,
        description: str = "🕊️ fly telegram v2"
    ):
        return self.viamanager.register_via(text, buttons, description)
    
    def update_via(self, id: str, **kwargs):
        self.viamanager.update(id, **kwargs)

    async def process_query(self, query: InlineQuery):
        q = query.strip()
        logging.debug("new inline query: %s", q)

        results = []
        if q.startswith("via_"):
            query_id = q.split("via_")[-1]
            if query_id in self.viamanager.results:
                result = self.viamanager.get_result(query_id)
                if result:
                    results.append(result)

        if results:
            await self._bot.answer_inline_query(
                inline_query_id=query.id,
                results=results,
                cache_time=300,
                is_personal=True
            )
        else:
            result = InlineQueryResultArticle(
                id="default",
                title="🕊️ fly telegram v2",
                description="Use via_ID for results.",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "<b>🕊️ fly telegram v2</b>\n",
                        "<b>Please, use via_(ID) for results.</b>"
                    ),
                    parse_mode="html"
                )
            )

            await self._bot.answer_inline_query(
                inline_query_id=query.id,
                results=[result],
                cache_time=300
            )


    def handler(self, callback_data: str = None):
        logging.debug(
        "Starting handler registration. Callback data provided: %s", callback_data)

        def decorator(func):
            handler_name = callback_data or func.__name__
            logging.debug("Registering handler '%s' for function '%s'",
                         handler_name, func.__name__)
            logging.debug("Function details: %s", func)

            func._is_handler = True
            func._handler_name = handler_name

            if handler_name in self.handlers:
                logging.debug(
                    "Handler '%s' is already registered. Overwriting it.", handler_name)

            self.handlers[handler_name] = func
            logging.debug("Handler '%s' successfully registered. Current handlers: %s",
                             handler_name, list(self.handlers.keys()))
            return func
        return decorator

    
    async def process_callback(self, callback_query: types.CallbackQuery):
        logging.debug("Callback query received. Data: %s", callback_query.data)
        logging.debug("Full callback query object: %s", callback_query)

        handler_name = callback_query.data
        logging.debug(
            "Processing callback query with handler name: %s", handler_name)
        logging.debug("Available handlers: %s", list(
            self.handlers.keys()))

        try:
            if handler_name in self.handlers:
                logging.debug(
                    "Handler '%s' found. Preparing to execute.", handler_name)
                call = InlineCall(callback_query)
                logging.debug("InlineCall object created: %s", call)
                logging.debug("InlineCall details: %s", call.__dict__)

                logging.debug("Executing handler '%s'...", handler_name)
                await self.handlers[handler_name](call)
                logging.debug("Handler '%s' executed successfully.", handler_name)
            else:
                logging.debug(
                    "No handler found for callback data: %s", handler_name)

        except Exception as e:
            logging.error("Error processing callback '%s': %s",
                          handler_name, str(e), exc_info=True)
            raise

    
    def register_handlers(self, dp: Dispatcher):
        logging.debug("Starting registration of callback query handler.")
        logging.debug("Dispatcher object: %s", self.dp)

        self.dp.register_callback_query_handler(self.process_callback, lambda c: True)
        logging.debug("Callback query handler registered successfully.")
        logging.debug("Current registered handlers in dispatcher: %s",
                     self.dp.message_handlers.handlers)

    async def start(self, client: Client):
        botmanager = BotManager()
        token = database.get('inline_token')

        if not token:
            inline_token = await botmanager.create(client)
            if not inline_token:
                raise ValueError("Failed to create inline bot!")
            else:
                inline_token = database.set('inline_token', inline_token)
        
        try:
            self._bot = Bot(token=token)
            Bot.set_current(self._bot)

            logging.debug("BOT method id: %s", id(self._bot))
            logging.debug("BOT value: %s", self._bot)
        except Unauthorized:
            database.set("inline_token", None)
            raise ValueError("Invalid token! restart the userbot.")
        
        self.dp = Dispatcher(self._bot)

        self.register_handlers(self.dp)
        logging.info("Inline bot is loaded.")
        asyncio.ensure_future(self.dp.start_polling())

    async def stop(self):
        await self._bot.close()
