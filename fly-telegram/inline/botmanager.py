#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import os
import random
import re
import string
import sys

from conversation import Conversation
from pyrogram import Client, errors

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BotManager:
    def __init__(self) -> None:
        self.errors_texts = [
            "Sorry.",
            "That I cannot do.",
            "too many attempts",
            "Unfortunately, you cannot create new bots at this time."
        ]

    async def create(self, client: Client,
                     botfather: str = "@BotFather") -> str:
        id = "".join(random.choice(string.ascii_letters + string.digits)
                     for _ in range(5))
        username = f"flyTG_{id}_bot"
        display_name = f"🕊 Fly-telegram of {client.me.first_name}"

        messages = [
            "/cancel",
            "/newbot",
            display_name,
            username,
            "/setinline",
            f"@{username}",
            "🕊 fly-telegram: ",
        ]

        token_pattern = r"Use this token to access the HTTP API:\n([0-9]+:[A-Za-z0-9_]+)"
        token = None

        async with Conversation(client, botfather, True) as conv:
            for message in messages:
                await asyncio.sleep(0.5)
                try:
                    await conv.send(message)
                    response = await conv.response(limit=2)
                    match = re.search(token_pattern, response.text)

                    if match:
                        token = match.group(1)

                    if any(error in response.text for error in self.errors_texts):
                        raise Exception(
                            f"Failed to create inline bot. Botfather response: {response.text}")
                except errors.UserIsBlocked:
                    await client.unblock_user(botfather)

            async with Conversation(client, f"@{username}", True) as conv:
                await conv.send("/start")

        return token
