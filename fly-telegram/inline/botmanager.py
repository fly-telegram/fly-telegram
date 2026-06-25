#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import logging
import random
import re
import string

from conversation import Conversation
from pyrogram import Client, errors


class BotManager:
    def __init__(self) -> None:
        """
        The inline bot manager
        """
        self.errors_texts = [
            "Sorry.",
            "That I cannot do.",
            "too many attempts",
            "Unfortunately, you cannot create new bots at this time."
        ]

    async def create(self, client: Client,
                     botfather: str = "@BotFather") -> str:
        """
        Create the inline bot

        Args:
            client (pyrogram.Client): The pyrogram object client
            botfather (str): BotFather username

        Returns:
            str: The bot token
        """
        bot_id = "".join(random.choice(string.ascii_letters + string.digits)
                         for _ in range(5))
        username = f"flyTG_{bot_id}_bot"
        display_name = f"🕊 Fly-telegram of {client.me.first_name}"

        pattern = r"{}:\n([0-9]+:[A-Za-z0-9_]+)"
        token = None

        async with Conversation(client, botfather, True) as conv:
            try:
                await conv.send("/cancel")
                await asyncio.sleep(1)
                await conv.send("/token")
                resp = await conv.response()
                if resp.reply_markup and resp.reply_markup.keyboard:
                    botpattern = re.compile(r"@?flyTG_[A-Za-z0-9]{5}_bot$")
                    for row in resp.reply_markup.keyboard:
                        for button in row:
                            if botpattern.fullmatch(button.text):
                                await conv.send(button.text)
                                token_resp = await conv.response()
                                if match := re.search(pattern.format("You can use this token to access HTTP API"), token_resp.text):
                                    token = match[1]
                                    username = button.text.lstrip("@")
                                break
                        if token:
                            break
            except Exception:
                pass

            if not token:
                messages = [
                    "/cancel",
                    "/newbot",
                    display_name,
                    username,
                    "/setinline",
                    f"@{username}",
                    "🕊 fly-telegram: ",
                ]

                for message in messages:
                    await asyncio.sleep(0.5)
                    try:
                        logging.debug(message)
                        await conv.send(message)
                        resp = await conv.response()
                        logging.debug(resp)

                        if match := re.search(pattern.format("Use this token to access the HTTP API"), resp.text):
                            token = match[1]

                        if any(error in resp.text for error in self.errors_texts):
                            raise Exception(
                                f"Failed to create inline bot. Botfather response: {resp.text}")
                    except (errors.UserIsBlocked, errors.YouBlockedUser):
                        await client.unblock_user(botfather)

        if token:
            async with Conversation(client, f"@{username}", True) as conv:
                await conv.send("/start")

        return token
