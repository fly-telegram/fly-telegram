#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import logging
from aiogram import Dispatcher, types
from .call import InlineCall
from datetime import datetime

handlers = {}

def handler(callback_data: str = None):
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

async def process_callback(callback_query: types.CallbackQuery):
    logging.debug("ID dict: %s", id(handlers))
    start_time = datetime.now()
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
    finally:
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logging.debug(
            "Callback query processing completed. Execution time: %.2f seconds", execution_time)


def register_handlers(dp: Dispatcher):
    logging.debug("Starting registration of callback query handler.")
    logging.debug("Dispatcher object: %s", dp)

    dp.register_callback_query_handler(process_callback, lambda c: True)
    logging.debug("Callback query handler registered successfully.")
    logging.debug("Current registered handlers in dispatcher: %s",
                 dp.message_handlers.handlers)
