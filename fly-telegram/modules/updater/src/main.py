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
from time import perf_counter

import git
from database import database
from inline import InlineCall
from loader import ConfigValue, Loader, ModuleConfig, events, validators

from .utils import check, origin, repo

loader = Loader()

config = ModuleConfig(ConfigValue("notify", True, "Notify for new updates", validators.Boolean()))


@events.loop(every=600)  # 10 min
async def check_updates(client):
    notify = config["notify"]
    if not notify and check():
        return

    chat_id = database.get("chats", "updates")
    if not chat_id:
        return

    inline = client.inline
    await inline.say(
        client,
        None,
        "🕊 <b>New update available!</b>",
        buttons=[
            [
                {
                    "text": "📥 Install!",
                    "callback": update_handler,
                }
            ]
        ],
        chat_id=chat_id,
    )


@events.on_load
async def on_load(client):
    if database.get("restart"):
        data = database.get("restart")
        database.set("restart", {})

        end = perf_counter() - data.get("time")
        text = data.get("text")

        if data.get("inline"):
            inline = client.inline
            await inline.bot.edit_message_text(
                text=text.format(f"{end:.3f}"), parse_mode="HTML", inline_message_id=data.get("message_id")
            )
            return

        await client.edit_message_text(
            chat_id=data.get("chat_id"), message_id=data.get("message_id"), text=data.get("text").format(f"{end:.3f}")
        )


async def restart_cmd(self):
    await self.message.edit("🕊 <b>Restarting...</b>")
    start = perf_counter()
    database.set(
        "restart",
        {
            "chat_id": self.message.chat.id,
            "message_id": self.message.id,
            "time": start,
            "text": "🕊 <b>Restarted! ({}s)</b>",
            "inline": False,
        },
    )

    os.execl(sys.executable, sys.executable, "-m", "fly-telegram")


@loader.alias("upd")
async def update_cmd(self):
    await self.message.delete()

    inline = self.client.inline
    await inline.say(
        self.client,
        self.message,
        "🕊 <b>Update now?</b>",
        buttons=[
            [
                {
                    "text": "✅ Yes",
                    "callback": update_handler,
                }
            ],
            [
                {
                    "text": "❌ No",
                    "callback": no_update_handler,
                }
            ],
        ],
    )


async def update_handler(call: InlineCall):
    branch = database.get("updater", "branch")
    if not check():
        await call.bot.edit_message_text(
            text="🕊 <b>Already installed latest version!</b>",
            parse_mode="HTML",
            inline_message_id=call.inline_message_id,
        )
        return

    start = perf_counter()

    database.set(
        "restart",
        {
            "chat_id": None,
            "message_id": call.inline_message_id,
            "time": start,
            "text": "🕊 <b>Updated! ({}s)</b>",
            "inline": True,
        },
    )

    await call.bot.edit_message_text(
        text="🕊 <b>Updating...</b>", parse_mode="HTML", inline_message_id=call.inline_message_id
    )

    try:
        origin.pull(branch)
    except git.GitCommandError:
        repo.git.reset("--hard")

    os.execl(sys.executable, sys.executable, "-m", "fly-telegram")


async def no_update_handler(call: InlineCall):
    await call.bot.edit_message_text(
        text="❌ <b>Cancelled</b>", parse_mode="HTML", inline_message_id=call.inline_message_id
    )
