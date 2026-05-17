#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import inspect
import json
import logging
import sys
import os
from uuid import uuid4

from aiogram import Bot, Dispatcher, Router
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQuery, InlineQueryResultArticle,
    InputTextMessageContent, CallbackQuery, ChosenInlineResult
)
from aiogram.exceptions import TelegramUnauthorizedError
from aiogram.utils.token import TokenValidationError
from database import database

from .botmanager import BotManager
from .call import InlineCall

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Via:
    def __init__(self):
        self.active = {}
        self.results = {}
        self.handlers = {}

    def add(self, text, prefix="via_", buttons=None, description="🕊️ fly telegram system result"):
        query_id = str(uuid4())
        input_text = InputTextMessageContent(
            message_text=text, parse_mode="HTML")
        reply_markup = None
        buttons_uuid = []

        if buttons:
            keyboard = []
            for brow in buttons:
                row = []
                for btn in brow:
                    if "switch_inline_query_current_chat" in btn:
                        row.append(InlineKeyboardButton(
                            text=btn.get("text", "button"),
                            switch_inline_query_current_chat=btn["switch_inline_query_current_chat"]
                        ))
                        continue
                    if "switch_inline_query" in btn:
                        row.append(InlineKeyboardButton(
                            text=btn.get("text", "button"),
                            switch_inline_query=btn["switch_inline_query"]
                        ))
                        continue

                    callback = btn.get('callback')
                    if not callable(callback):
                        raise TypeError("callback must be callable")

                    uid = str(uuid4())
                    buttons_uuid.append(uid)
                    self.handlers[uid] = {
                        "callback": callback, **({"params": btn["params"]} if "params" in btn else {})}
                    row.append(InlineKeyboardButton(
                        text=btn.get("text", "button"), callback_data=uid))
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
            "text": text, "reply_markup": buttons, "prefix": prefix, "buttons_uuid": buttons_uuid}
        self.results[query_id] = result
        return query_id

    def get_result(self, id):
        return self.results.get(id)

    def get_huuid(self, uuid):
        if data := self.handlers.get(uuid):
            return data.get("callback"), data.get("params", {})
        return None, None

    def update(self, id, **kwargs):
        if id not in self.active:
            return
        old = self.active[id]
        for uid in old.get("buttons_uuid", []):
            self.handlers.pop(uid, None)
        old.update(kwargs)

        if "buttons" in kwargs:
            new_uuid = []
            if buttons := kwargs["buttons"]:
                keyboard = []
                for brow in buttons:
                    row = []
                    for btn in brow:
                        cb = btn.get("callback")
                        if not callable(cb):
                            raise TypeError("callback must be callable")
                        uid = str(uuid4())
                        self.handlers[uid] = {
                            "callback": cb, **({"params": btn["params"]} if "params" in btn else {})}
                        new_uuid.append(uid)
                        row.append(InlineKeyboardButton(
                            text=btn.get("text", "button"), callback_data=uid))
                    keyboard.append(row)
                old["reply_markup"] = InlineKeyboardMarkup(
                    inline_keyboard=keyboard)
            old["buttons_uuid"] = new_uuid
            if id in self.results:
                self.results[id].reply_markup = old.get("reply_markup")

        if "text" in kwargs and id in self.results:
            self.results[id].input_message_content.message_text = kwargs["text"]


class Inline:
    def __init__(self):
        self.client = None
        self._bot: Bot = None
        self.dp: Dispatcher = None
        self._router: Router = None
        self.viamanager = Via()

    @property
    def bot(self) -> Bot:
        return self._bot

    async def say(self, client, message, text, buttons=None, **kwargs):
        query_id = self.viamanager.add(text, kwargs.get(
            "prefix", "via_"), buttons, kwargs.get("description", ""))
        me = await self.bot.get_me()
        results = await client.get_inline_bot_results(me.username, f"via_{query_id}")
        await client.send_inline_bot_result(
            chat_id=kwargs.get(
                "chat_id", message.chat.id if message else None),
            query_id=results.query_id,
            result_id=results.results[0].id,
            message_thread_id=(message.topic.id if message and getattr(
                message, "topic", None) else None),
        )
        return query_id

    def via(self, text, prefix="via_", buttons=None, description="🕊️ fly telegram v2"):
        return self.viamanager.add(text, prefix, buttons, description)

    def update_via(self, id, **kwargs):
        self.viamanager.update(id, **kwargs)

    async def process_query(self, query: InlineQuery):
        q = query.query
        me = self.client.me

        if query.from_user.id != me.id:
            await query.answer(results=[InlineQueryResultArticle(
                id="notprems", title="🕊️ fly telegram v2", description="Not available",
                input_message_content=InputTextMessageContent(
                    message_text="<b>🕊️ fly telegram v2</b>\n<b>Not available for you</b>", parse_mode="html"
                )
            )], cache_time=20)
            return

        # Configurator queries
        if q.startswith("cfg_"):
            await self._cfg_query(query)
            return

        results = []
        if "_" in q:
            query_id = q.split("_")[-1]
            if query_id in self.viamanager.results:
                results.append(self.viamanager.get_result(query_id))

        if results:
            await query.answer(results=results, cache_time=20, is_personal=True)
            return

        await query.answer(results=[InlineQueryResultArticle(
            id="default", title="🕊️ fly telegram v2", description="Not found!",
            input_message_content=InputTextMessageContent(
                message_text="<b>🕊️ fly telegram v2</b>\n<b>The query is not found</b>", parse_mode="html"
            )
        )], cache_time=20, is_personal=True)

    async def process_chosen_result(self, result: ChosenInlineResult):
        if result.query.startswith("cfg_"):
            await self._cfg_chosen(result)

    async def process_callback(self, callback_query: CallbackQuery):
        data = callback_query.data
        call = InlineCall(callback_query, self.client, self._bot)

        if call.from_user.id != self.client.me.id:
            await call.answer("❌ Not for you")
            return

        # Configurator callbacks
        if data.startswith("confirm_") or data.startswith("cancel_"):
            await self._cfg_callback(call)
            return

        func, params = self.viamanager.get_huuid(data)
        if func:
            try:
                sig = inspect.signature(func)
                if params and len(sig.parameters) > 1:
                    await func(call, **params)
                else:
                    await func(call)
            except Exception as e:
                logging.error(f"Callback error: {e}")
                await call.answer("❌ Callback processing error.")
        else:
            await call.answer("⚠️ Handler expired")

    async def _cfg_query(self, query: InlineQuery):
        q = query.query
        parts = q.split(maxsplit=1)
        uid = parts[0]
        new_val = parts[1] if len(parts) > 1 else ""

        edit = self.viamanager.handlers.get(uid)
        if not edit or "module" not in edit:
            await query.answer(results=[InlineQueryResultArticle(
                id="expired", title="⚠️ Handler expired", description="Go back and try again",
                input_message_content=InputTextMessageContent(
                    message_text="⚠️ <b>Handler expired!</b>", parse_mode="HTML"
                )
            )], cache_time=0, is_personal=True)
            return

        module, key, _vtype = edit["module"], edit["key"], edit["vtype"]
        from modules.configurator.src.utils import get as cfg_get
        cur = cfg_get(module, key, "")

        text = (
            f"🕊 <b>Confirm editing</b> <code>{module}</code>\n\n"
            f"├─ <i>key</i>: <code>{key}</code>\n"
            f"├─ <i>old:</i>: <code>{cur}</code>\n"
            f"└─ <i>new:</i>: <code>{new_val}</code>"
        )

        save_id = str(uuid4())
        cancel_id = str(uuid4())
        self.viamanager.handlers[f"confirm_{save_id}"] = {
            "action": "save", "module": module, "key": key, "value": new_val, "uid": uid}
        self.viamanager.handlers[f"cancel_{cancel_id}"] = {
            "action": "cancel", "module": module, "key": key, "uid": uid}

        markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="✅ Save", callback_data=f"confirm_{save_id}"),
            InlineKeyboardButton(
                text="❌ Cancel", callback_data=f"cancel_{cancel_id}"),
        ]])

        await query.answer(results=[InlineQueryResultArticle(
            id=str(uuid4()), title="🕊 Enter new value",
            description=f"{cur} to {new_val}",
            input_message_content=InputTextMessageContent(
                message_text=text, parse_mode="HTML"),
            reply_markup=markup,
        )], cache_time=0, is_personal=True)

    async def _cfg_chosen(self, result: ChosenInlineResult):
        q = result.query
        if not q.startswith("cfg_"):
            return

        parts = q.split(maxsplit=1)
        uid = parts[0]
        value = parts[1] if len(parts) > 1 else ""

        edit = self.viamanager.handlers.get(uid)
        if not edit or "module" not in edit:
            return

        module, key = edit["module"], edit["key"]
        try:
            from modules.configurator.src.utils import set as cfg_set
            cfg_set(module, key, value)
            self.viamanager.handlers.pop(uid, None)
            await self._bot.send_message(
                chat_id=self.client.me.id,
                text=(
                    "✅ <b>Saved!</b>\n"
                    f"<code>{module}.{key} = {value}</code>"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Config save error: {e}")

    async def _cfg_callback(self, call: InlineCall):
        data = call.data
        h = self.viamanager.handlers

        if data.startswith("confirm_"):
            d = h.get(data)
            if d and d.get("action") == "save":
                module, key, value, uid = d["module"], d["key"], d["value"], d["uid"]
                try:
                    from modules.configurator.src.utils import set as cfg_set
                    cfg_set(module, key, value)
                    h.pop(uid, None)
                    h.pop(data, None)
                    await self._bot.edit_message_text(
                        text=(
                            "✅ <b>Saved!</b>\n"
                            f"<code>{module}.{key} = {value}</code>"
                        ),
                        inline_message_id=call.inline_message_id, parse_mode="HTML"
                    )
                except Exception as e:
                    logging.error(f"Config save error: {e}")
                    await self._bot.edit_message_text(text=f"❌ <b>Error:</b> <code>{e}</code>",
                                                      inline_message_id=call.inline_message_id, parse_mode="HTML")

        elif data.startswith("cancel_"):
            d = h.get(data)
            if d and d.get("action") == "cancel":
                h.pop(d["uid"], None)
                h.pop(data, None)
                await self._bot.edit_message_text(
                    text="❌ <b>Cancelled</b>",
                    inline_message_id=call.inline_message_id, 
                    parse_mode="HTML"
                )

    def register_handlers(self, dp: Dispatcher):
        self._router = Router()
        self._router.callback_query.register(self.process_callback)
        self._router.inline_query.register(self.process_query)
        self._router.chosen_inline_result.register(self.process_chosen_result)
        dp.include_router(self._router)

    async def start(self, client, many_token=None):
        botmanager = BotManager()

        if many_token:
            token = many_token
            database.set("inline_token", token)
        else:
            token = database.get("inline_token")
            if not token:
                token = await botmanager.create(client)
                if not token:
                    raise ValueError("Failed to create inline bot!")
                database.set("inline_token", token)

        with open("config.json") as f:
            config = json.load(f)

        proxy = config.get("proxy")
        proxy_url = None
        if proxy and proxy.get("scheme") and proxy.get("hostname") and proxy.get("port"):
            proxy_url = f"{proxy['scheme']}://{proxy['hostname']}:{proxy['port']}"

        try:
            if proxy_url:
                from aiogram.client.session.aiohttp import AiohttpSession
                self._bot = Bot(
                    token=token, session=AiohttpSession(proxy=proxy_url))
            else:
                self._bot = Bot(token=token)
        except (TelegramUnauthorizedError, TokenValidationError) as e:
            logging.error(f"Invalid token: {e}")
            database.set("inline_token", None)
            raise ValueError("Invalid token! restart the userbot.") from e
        except Exception as e:
            logging.error(
                f"Failed to create inline bot: {type(e).__name__}: {e}")
            raise

        self.dp = Dispatcher()
        self.client = client
        self.register_handlers(self.dp)
        logging.info("Inline bot loaded.")
        asyncio.create_task(self.dp.start_polling(
            self._bot, skip_updates=True, handle_signals=False))

    async def stop(self):
        if self._bot:
            await self._bot.session.close()
