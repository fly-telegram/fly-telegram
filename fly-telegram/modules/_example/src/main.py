#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

"""The example module"""

from inline import InlineCall


async def command_cmd(self):
    """The example command"""
    await self.message.delete()
    inline = self.client.inline
    await inline.say(
        client=self.client,
        message=self.message,
        text=self.lang.get("title"),
        buttons=[
            [
                {
                    "text": self.lang.get("test_button"),
                    "callback": bot_reply,
                    "params": {"text": self.lang.get("hint")},
                }
            ]
        ],
    )


async def bot_reply(call: InlineCall, text: str):
    """The example callback handler"""
    await call.answer(text)
