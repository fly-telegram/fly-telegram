#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

from aiogram.types import CallbackQuery
from pyrogram import Client


class InlineCall:
    def __init__(self, callback_query: CallbackQuery, client: Client = None, bot=None):
        """
        InlineCall object
        Args:
            callback_query (aiogram.types.CallbackQuery): The callback query
            client (pyrogram.Client): The pyrogram client object
            bot (aiogram.Bot): The bot object
        """
        self.callback_query = callback_query
        self.inline_message_id = callback_query.inline_message_id
        self.message = callback_query.message
        self.data = callback_query.data
        self.from_user = callback_query.from_user
        self.bot = bot
        self.client = client

    async def answer(self, text: str = None, show_alert: bool = False):
        """
        Answer from inline bot
        Args:
            text (str): The text message
            show_alert (bool): Show the alert
        """
        await self.callback_query.answer(text=text, show_alert=show_alert)

    async def edit_message(self, text: str, reply_markup=None):
        """
        Edit the message from inlinebot
        Args:
            text (str): The text message
            reply_markup: The buttons
        """
        if self.inline_message_id:
            await self.bot.edit_message_text(
                text=text,
                inline_message_id=self.inline_message_id,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
        elif self.message:
            await self.message.edit_text(text, reply_markup=reply_markup)
