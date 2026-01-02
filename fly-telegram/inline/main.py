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

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from .call import InlineCall

handlers = {}

class Inline:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot)

    def handler(self, callback_data: str = None):
        logging.debug(
        "Starting handler registration. Callback data provided: %s", callback_data)

        def decorator(func):
            handler_name = callback_data or func.__name__
            logging.debug("ID dict: %s", id(handlers))
            logging.debug("Registering handler '%s' for function '%s'",
                         handler_name, func.__name__)
            logging.debug("Function details: %s", func)

            if handler_name in handlers:
                logging.debug(
                    "Handler '%s' is already registered. Overwriting it.", handler_name)

            handlers[handler_name] = func
            logging.debug("Handler '%s' successfully registered. Current handlers: %s",
                             handler_name, list(handlers.keys()))
            return func
        return decorator

    
    async def process_callback(self, callback_query: types.CallbackQuery):
        logging.debug("Callback query received. Data: %s", callback_query.data)
        logging.debug("Full callback query object: %s", callback_query)

        handler_name = callback_query.data
        logging.debug(
            "Processing callback query with handler name: %s", handler_name)
        logging.debug("Available handlers: %s", list(
            handlers.keys()))

        try:
            if handler_name in handlers:
                logging.debug(
                    "Handler '%s' found. Preparing to execute.", handler_name)
                call = InlineCall(callback_query)
                logging.debug("InlineCall object created: %s", call)
                logging.debug("InlineCall details: %s", call.__dict__)

                logging.debug("Executing handler '%s'...", handler_name)
                await handlers[handler_name](call)
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

        dp.register_callback_query_handler(self.process_callback, lambda c: True)
        logging.debug("Callback query handler registered successfully.")
        logging.debug("Current registered handlers in dispatcher: %s",
                     self.dp.message_handlers.handlers)

    async def start(self):
        self.register_handlers(self.dp)
        logging.info("Inline bot is loaded.")
        asyncio.ensure_future(self.dp.start_polling())

    async def stop(self):
        await self.bot.close()
