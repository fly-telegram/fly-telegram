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

from aiogram import Bot, Dispatcher, types
from aiogram.utils.exceptions import Unauthorized

from pyrogram import Client

from .call import InlineCall
from .botmanager import BotManager
from database import database

class Inline:
    def __init__(self):
        self.bot = None
        self.dp = None
        logging.debug("New instance: %s", id(self))

        # suka, takoi govnokod nize, no ia zaebalsa. kto pofixit eto - pull request pls. ia ne znay chto delat....
        if '_inline' not in sys.modules:
            sys.modules['_inline'] = {'handlers': {}}
        elif 'handlers' not in sys.modules['_inline']:
            sys.modules['_inline']['handlers'] = {}

        self.handlers = sys.modules['_inline']['handlers']

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
            self.bot = Bot(token=token)
        except Unauthorized:
            database.set("inline_token", None)
            raise ValueError("Invalid token! restart the userbot.")
        
        self.dp = Dispatcher(self.bot)

        self.register_handlers(self.dp)
        logging.info("Inline bot is loaded.")
        asyncio.ensure_future(self.dp.start_polling())

    async def stop(self):
        await self.bot.close()
