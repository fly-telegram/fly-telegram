#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import logging
from aiogram import Dispatcher, types
from .call import InlineCall
from datetime import datetime


class HandlersManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logging.info("Initializing HandlersManager singleton instance")
            cls._instance = super(HandlersManager, cls).__new__(cls)
            cls._instance.loaded_handlers = {}
            logging.info("HandlersManager initialized. Loaded handlers: %s",
                         cls._instance.loaded_handlers)
        return cls._instance

    def handler(self, callback_data: str = None):
        logging.info(
            "Starting handler registration. Callback data provided: %s", callback_data)

        def decorator(func):
            handler_name = callback_data or func.__name__
            logging.info("Registering handler '%s' for function '%s'",
                         handler_name, func.__name__)
            logging.info("Function details: %s", func)

            if handler_name in self.loaded_handlers:
                logging.warning(
                    "Handler '%s' is already registered. Overwriting it.", handler_name)

            self.loaded_handlers[handler_name] = func
            logging.info("Handler '%s' successfully registered. Current handlers: %s",
                         handler_name, list(self.loaded_handlers.keys()))
            return func
        return decorator


handlers_manager = HandlersManager()


async def process_callback(callback_query: types.CallbackQuery):
    start_time = datetime.now()
    logging.info("Callback query received. Data: %s", callback_query.data)
    print(handlers_manager.loaded_handlers)
    logging.info("Full callback query object: %s", callback_query)

    handler_name = callback_query.data
    logging.info(
        "Processing callback query with handler name: %s", handler_name)
    logging.info("Available handlers: %s", list(
        handlers_manager.loaded_handlers.keys()))

    try:
        if handler_name in handlers_manager.loaded_handlers:
            logging.info(
                "Handler '%s' found. Preparing to execute.", handler_name)
            call = InlineCall(callback_query)
            logging.info("InlineCall object created: %s", call)
            logging.info("InlineCall details: %s", call.__dict__)

            logging.info("Executing handler '%s'...", handler_name)
            await handlers_manager.loaded_handlers[handler_name](call)
            logging.info("Handler '%s' executed successfully.", handler_name)
        else:
            logging.warning(
                "No handler found for callback data: %s", handler_name)

    except Exception as e:
        logging.error("Error processing callback '%s': %s",
                      handler_name, str(e), exc_info=True)
        raise
    finally:
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logging.info(
            "Callback query processing completed. Execution time: %.2f seconds", execution_time)


def register_handlers(dp: Dispatcher):
    logging.info("Starting registration of callback query handler.")
    logging.info("Dispatcher object: %s", dp)

    dp.register_callback_query_handler(process_callback, lambda c: True)
    logging.info("Callback query handler registered successfully.")
    logging.info("Current registered handlers in dispatcher: %s",
                 dp.message_handlers.handlers)
