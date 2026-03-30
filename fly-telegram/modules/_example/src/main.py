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
                    "callback": bot_reply,           # your handler. callable function.
                    "params": {                      # function params
                        "text": "inline is easy"     # key: value
                    }
                }
            ]
        ]
    )


# your handler
async def bot_reply(call: InlineCall, text: str):    # InlineCall, "inline is easy"
    await call.answer(text)                          # return answer


