#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

from aiogram.types import CallbackQuery


class InlineCall:
    def __init__(self, callback_query: CallbackQuery):
        self.callback_query = callback_query
        self.inline_message_id = callback_query.inline_message_id
        self.data = callback_query.data
        self.from_user = callback_query.from_user
        print(f"Callback data: {self.data}")

    async def answer(self, text: str = None, show_alert: bool = False):
        await self.callback_query.answer(text, show_alert=show_alert)

    async def edit_message(self, text: str, reply_markup=None):
        await self.callback_query.message.edit_text(text, reply_markup=reply_markup)
