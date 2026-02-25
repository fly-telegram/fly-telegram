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
import sys
from typing import Optional
from uuid import uuid4

from aiogram import Bot, Dispatcher, types
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           InlineQuery, InlineQueryResultArticle,
                           InputTextMessageContent)
from aiogram.utils.exceptions import Unauthorized
from database import database
from pyrogram import Client
from pyrogram.types import Message

from .botmanager import BotManager
from .call import InlineCall

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Via:
    def __init__(self) -> None:
        if '_via' not in sys.modules:
            sys.modules['_via'] = {
                'active': {},
                'results': {},
                'handlers': {}
            }

        self.active = sys.modules['_via']['active']
        self.results = sys.modules['_via']['results']
        self.handlers = sys.modules['_via']['handlers']

    def add(
        self,
        text: str,
        prefix: str = "via_",
        buttons: Optional[list[list[dict]]] = None,
        description: str = "🕊️ fly telegram system result",
    ):
        query_id = str(uuid4())
        input_text = InputTextMessageContent(
            message_text=text,
            parse_mode="HTML"
        )

        reply_markup = None
        buttons_uuid = []

        if buttons:
            keyboard = []

            for brow in buttons:
                row = []
                for btn in brow:
                    callback = btn.get('callback')
                    if not callable(callback):
                        raise TypeError("callback must be a callable!")

                    button_uuid = str(uuid4())
                    buttons_uuid.append(button_uuid)
                    self.handlers[button_uuid] = callback

                    row.append(
                        InlineKeyboardButton(
                            text=btn.get("text", "button"),
                            callback_data=button_uuid
                        )
                    )
                keyboard.append(row)
            reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        result = InlineQueryResultArticle(
            id=f"{prefix}{query_id}",
            title="🕊️ fly telegram v2",
            description=description,
            input_message_content=input_text,
            reply_markup=reply_markup,
        )

        self.active[query_id] = {
            "text": text,
            "reply_markup": buttons,
            "prefix": prefix,
            "buttons_uuid": buttons_uuid
        }

        self.results[query_id] = result

        return query_id

    def get_result(self, id: str):
        logging.debug(self.results)
        return self.results[id]

    def get_huuid(self, uuid: str):
        logging.debug(self.handlers)
        return self.handlers.get(uuid)

    def update(self, id: str, **kwargs):
        if id in self.active:
            old = self.active[id]
            for old_uuid in old.get('buttons_uuid', []):
                self.handlers.pop(old_uuid, None)
            old.update(kwargs)

            if "buttons" in kwargs:
                buttons = kwargs["buttons"]
                reply_markup = None
                new_uuid = []
                if buttons:
                    keyboard = []
                    for brow in buttons:
                        row = []
                        for btn in brow:
                            callback_func = btn.get("callback")
                            if not callable(callback_func):
                                raise TypeError("callback must be a callable!")
                            btn_uuid = str(uuid4())
                            self.handlers[btn_uuid] = callback_func
                            new_uuid.append(btn_uuid)
                            row.append(
                                InlineKeyboardButton(
                                    text=btn.get("text", "button"),
                                    callback_data=btn_uuid
                                )
                            )
                        keyboard.append(row)
                    reply_markup = InlineKeyboardMarkup(
                        inline_keyboard=keyboard)
                old["buttons_uuid"] = new_uuid
                if id in self.results:
                    self.results[id].reply_markup = reply_markup

            if "text" in kwargs and id in self.results:
                self.results[id].input_message_content.message_text = kwargs["text"]


class Inline:
    def __init__(self):
        self.client = None
        self._bot: Bot = None
        self.dp: Dispatcher = None
        logging.debug("New instance: %s", id(self))
        self.viamanager = Via()

    async def say(
            self,
            client: Client,
            message: Message,
            text: str,
            buttons: Optional[list[list[dict]]] = None,
            **kwargs) -> str:
        query_id = self.viamanager.add(
            text,
            kwargs.get('prefix', 'via_'),
            buttons,
            kwargs.get('description', '')
        )

        me = await self.bot.get_me()
        results = await client.get_inline_bot_results(me.username, f"via_{query_id}")

        await client.send_inline_bot_result(
            chat_id=kwargs.get('chat_id', message.chat.id if message else None),
            query_id=results.query_id,
            result_id=results.results[0].id,
            message_thread_id=(
                getattr(message, 'topic', None)
                and message.topic.id
                if not message is None
                else None
            )
        )
        return query_id

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

    async def process_callback(self, callback_query: types.CallbackQuery):
        huuid = callback_query.data
        call = InlineCall(callback_query, self.client, self._bot)
        if call.from_user.id != self.client.me.id:
            await call.answer("❌ Not for you")
            return

        func = self.viamanager.get_huuid(huuid)
        if func:
            await func(call)
        else:
            await call.answer("⚠️ Handler expired")

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
