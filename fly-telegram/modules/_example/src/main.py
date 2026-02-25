#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

"""The example module"""

from inline import InlineCall, inline  # /fly-telegram/inline


# _cmd is required for command functions
async def command_cmd(self):
    await self.client.unblock_user("spambot")        # use pyrogram client
    await self.message.delete()
    await inline.say(                                # say with inline bot
        client=self.client,                          # pyrogram reply
        message=self.message,                        # your message object
        text="inline the easy!",                     # message text
        buttons=[
            [                                        # row. btn | btn | btn
                {
                    "text": "test",                  # the button name
                    # callback. callable function.
                    "callback": bot_reply
                }
            ]
        ]
    )

# your handler


async def bot_reply(call: InlineCall):
    await call.answer("inline is easy!")             # return answer
