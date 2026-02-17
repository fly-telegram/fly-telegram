#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

import os
import sys

import git
from database import database
from inline import InlineCall, inline
from loader import Loader

from .utils import check, origin, repo

loader = Loader()


@loader.alias("upd")
async def update_cmd(self):
    await self.message.delete()

    await inline.say(
        self.client,
        self.message,
        "🕊 <b>Update now?</b>",
        prefix="help_update_"
        buttons=[
            [{"text": "✅ Yes"}],
            [{"text": "❌ No"}]
        ]
    )


@inline.handler(r"help_update_(.+)_0")
async def update(call: InlineCall):
    branch = database.get("updater", "branch")
    if not check():
        await call.bot.edit_message_text(
            text='🕊 <b>Installed latest version!</b>',
            parse_mode="HTML",
            inline_message_id=call.inline_message_id
        )
        return

    await call.bot.edit_message_text(
        text='🕊 <b>Updating...</b>',
        parse_mode="HTML",
        inline_message_id=call.inline_message_id
    )

    try:
        origin.pull(branch)
    except git.GitCommandError:
        repo.git.reset("--hard")

    os.execl(
        sys.executable,
        sys.executable,
        "-m", "fly-telegram")


@inline.handler(r"help_update_(.+)_1")
async def no_update(call: InlineCall):
    await call.bot.edit_message_text(
        text='❌ <b>Cancelled</b>',
        parse_mode="HTML",
        inline_message_id=call.inline_message_id
    )
