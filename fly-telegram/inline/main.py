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
import re
import sys
from typing import Optional, Union
from uuid import uuid4

from aiogram import Bot, Dispatcher, types
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           InlineQuery, InlineQueryResultArticle,
                           InputTextMessageContent)
from aiogram.utils.exceptions import Unauthorized
from database import database
from pyrogram import Client

from .botmanager import BotManager
from .call import InlineCall

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Via:
    def __init__(self) -> None:
        if '_via' not in sys.modules:
            sys.modules['_via'] = {'active': {}, 'results': {}}

        self.active = sys.modules['_via']['active']
        self.results = sys.modules['_via']['results']

    def add(
        self,
        text: str,
        prefix: str = "via_",
        buttons: Optional[list[list[dict]]] = None,
        description: str = "Fly-Telegram system result.",
    ):
        query_id = str(uuid4())
        input_text = InputTextMessageContent(
            message_text=text,
        )

        reply_markup = None
        if buttons:
            keyboard = []
            count = 0

            for brow in buttons:
                row = []
                for btn in brow:
                    row.append(
                        InlineKeyboardButton(
                            text=btn.get("text", "button"),
                            callback_data=btn.get(
                                "callback", f"{prefix}{query_id}_{count}")
                        )
                    )
                    count += 1
                keyboard.append(row)
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        result = InlineQueryResultArticle(
            id=f"{prefix}{query_id}",
            title="🕊️ fly telegram v2",
            description=description,
            input_message_content=input_text,
            reply_markup=reply_markup
        )

        self.active[query_id] = {
            "text": text,
            "reply_markup": buttons,
            "prefix": prefix
        }

        self.results[query_id] = result

        return query_id

    def get_result(self, id: str):
        logging.debug(self.results)
        return self.results[id]

    def update(self, id: str, **kwargs):
        if id in self.active:
            self.active[id].update(kwargs)
            prefix = self.results[id].get("prefix")
            if id in self.results:
                result = self.results[id]
                if "text" in kwargs:
                    result.input_message_content.message_text = kwargs["text"]
                if "buttons" in kwargs:
                    if kwargs["buttons"]:
                        keyboard = []
                        count = 0

                        for brow in kwargs["buttons"]:
                            row = []
                            for btn in brow:
                                row.append(
                                    InlineKeyboardButton(
                                        text=btn.get("text", "button"),
                                        callback_data=btn.get(
                                            "callback", f"{prefix}{id}_{len(keyboard)}")
                                    )
                                )
                                count += 1
                                keyboard.append(row)
                        result.reply_markup = InlineKeyboardMarkup(
                            inline_keyboard=keyboard)
                    else:
                        result.reply_markup = None


class Inline:
    def __init__(self):
        self.client = None
        self._bot: Bot = None
        self.dp: Dispatcher = None
        self.viamanager = Via()
        logging.debug("New instance: %s", id(self))

        # suka, takoi govnokod nize, no ia zaebalsa. kto pofixit eto - pull request pls. ia ne znay chto delat....
        if '_inline' not in sys.modules:
            sys.modules['_inline'] = {'handlers': {}}
        elif 'handlers' not in sys.modules['_inline']:
            sys.modules['_inline']['handlers'] = {}

        self.handlers = sys.modules['_inline']['handlers']

    async def say(
        self,
        client: Client,
        chat_id: Union[int, str],
        text: str,
        prefix: str = "via_",
        buttons: Optional[list[list[dict]]] = None,
        description: str = "🕊️ fly telegram v2",
    ) -> str:
        uuid = self.viamanager.add(text, prefix, buttons, description)

        me = await self.bot.get_me()
        results = await client.get_inline_bot_results(
            me.username,
            f"{prefix}{uuid}"
        )

        await client.send_inline_bot_result(
            chat_id,
            results.query_id,
            results.results[0].id
        )
        return uuid

    def via(
        self,
        text: str,
        prefix: str = "via_",
        buttons: Optional[list[list[dict]]] = None,
        description: str = "🕊️ fly telegram v2",
    ):
        return self.viamanager.add(text, prefix, buttons, description)

    def update_via(self, id: str, **kwargs):
        self.viamanager.update(id, **kwargs)

    async def process_query(self, query: InlineQuery):
        q = query.query
        me = self.client.me

        if query.from_user.id != me.id:
            notprems = InlineQueryResultArticle(
                id="notprems",
                title="🕊️ fly telegram v2",
                description="Not available",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        "<b>🕊️ fly telegram v2</b>\n"
                        "<b>Not available for you</b>"
                    ),
                    parse_mode="html"
                )
            )

            await self._bot.answer_inline_query(
                inline_query_id=query.id,
                results=[notprems],
                cache_time=20
            )
            return

        results = []

        if "_" in q:
            query_id = q.split("_")[-1]
            logging.debug("found new via! ID: %s", query_id)

            if query_id in self.viamanager.results:
                default = self.viamanager.get_result(query_id)
                if default:
                    results.append(default)

        if results:
            await self._bot.answer_inline_query(
                inline_query_id=query.id,
                results=results,
                cache_time=20,
                is_personal=True
            )
            return

        default = InlineQueryResultArticle(
            id="default",
            title="🕊️ fly telegram v2",
            description="Not found!",
            input_message_content=InputTextMessageContent(
                message_text=(
                    "<b>🕊️ fly telegram v2</b>\n"
                    "<b>The query is not found</b>"
                ),
                parse_mode="html"
            )
        )

        await self._bot.answer_inline_query(
            inline_query_id=query.id,
            results=[default],
            cache_time=20,
            is_personal=True
        )

    def handler(self, callback_data: str = None):
        logging.debug(
            "Starting handler registration. Callback data provided: %s", callback_data)

        def decorator(func):
            handler_name = callback_data or func.__name__

            pattern = (
                f"^{handler_name}$"
                if not handler_name.startswith('^')
                else handler_name
            )

            logging.debug("Registering handler '%s' for function '%s'",
                          handler_name, func.__name__)
            logging.debug("Function details: %s", func)

            func._is_handler = True
            func._handler_name = handler_name

            self.handlers[re.compile(pattern)] = func
            logging.debug("Handler '%s' successfully registered. Current handlers: %s",
                          handler_name, list(self.handlers.keys()))
            return func
        return decorator

    async def process_callback(self, callback_query: types.CallbackQuery):
        handler_name = callback_query.data
        call = InlineCall(callback_query)
        me = self.client.me

        if call.from_user.id != me.id:
            await call.answer("❌ Not available for you")
            return

        for pattern, func in self.handlers.items():
            if pattern.match(handler_name):
                await func(call)
                return

        logging.debug("no regex match for: %s", handler_name)

    def register_handlers(self, dp: Dispatcher):
        logging.debug("Starting registration of callback query handler.")
        logging.debug("Dispatcher object: %s", self.dp)

        self.dp.register_callback_query_handler(
            self.process_callback, lambda c: True)
        logging.debug("Callback query handler registered successfully.")
        logging.debug("Current registered handlers in dispatcher: %s",
                      self.dp.message_handlers.handlers)

        self.dp.register_inline_handler(self.process_query, lambda q: True)

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
        self.client = client

        self.register_handlers(self.dp)
        logging.info("Inline bot is loaded.")
        asyncio.ensure_future(self.dp.start_polling())

    async def stop(self):
        await self._bot.close()
