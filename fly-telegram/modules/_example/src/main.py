#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

"""The example module"""

from inline import InlineCall, inline, make_keyboard  # /fly-telegram/inline


# _cmd is required for command functions
async def command_cmd(self):
    await self.client.unblock_user("spambot")        # use pyrogram client
    await inline.bot.send_message(                   # inline example usage
        self.client.me.id,                           # get user id from pyrogram client
        "🔥 WOW! click for magic",                   # message
        reply_markup=make_keyboard([                 # make_keyboard return InlineKeyboardMarkup
            {
                "text": "click",                     # button name
                "callback": "example"                # callback data
            }
        ])
    )
    await self.message.edit("🔥 <b>Inline command is sended. check DM</b>")


# register handler. callback_data: str = function name
@inline.handler(callback_data="example")
async def bot_reply(call: InlineCall):
    await call.answer("inline is easy!")             # return answer
