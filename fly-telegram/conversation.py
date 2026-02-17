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
from typing import Optional, Union

from pyrogram import Client, types


class Conversation:
    """
    A context manager for a conversation with a Telegram chat.

    Args:
        client (Client): The Telegram client instance.
        chat (Union[str, int]): The chat ID or username.
        clear (bool, optional): Whether to clear the conversation messages when exiting. Defaults to False.

    Attributes:
        client (Client): The Telegram client instance.
        chat (Union[str, int]): The chat ID or username.
        clear (bool): Whether to clear the conversation messages when exiting.
    """

    def __init__(
        self,
        client: Client,
        chat: Union[str, int],
        clear: bool = False
    ) -> None:
        self.client = client
        self.chat = chat
        self.clear = clear

        self.last = 0
        self.timeout = 10

    async def __aenter__(self) -> "Conversation":
        """
        Enters the conversation context.
        """
        try:
            async for message in self.client.get_chat_history(self.chat, limit=1):
                self.last = message.id
        except Exception:
            self.last = 0
        return self

    async def __aexit__(
        self,
        exc_type: type,
        exc_value: Exception,
        exc_traceback
    ) -> bool:
        """
        Exits the conversation context.

        If an exception occurs, logs the exception. If `clear` is True, clears the conversation messages.
        """
        if all(
            [exc_type, exc_value, exc_traceback]
        ):
            logging.exception(exc_value)
        else:
            if self.clear:
                await self.clear_messages()

        return True

    async def send(self, text: str, *args, **kwargs) -> types.Message:
        """
        Sends a message to the chat.

        Args:
            text (str): The message text.
            *args: Additional arguments for the `send_message` method.
            **kwargs: Additional keyword arguments for the `send_message` method.

        Returns:
            types.Message: The sent message.
        """
        message = await self.client.send_message(
            self.chat, text, *args, **kwargs)
        self.last = message.id
        return message

    async def response(self, timeout: Optional[int] = None) -> types.Message:
        """
        Waits for a response from the chat.

        Args:
            timeout (int, optional): The timeout in seconds. Defaults to 30.
            limit (int, optional): The maximum number of messages to retrieve. Defaults to 1.

        Returns:
            types.Message: The received response message.

        Raises:
            RuntimeError: If the timeout is reached.
        """
        timeout = timeout or self.timeout

        while timeout > 0:
            async for message in self.client.get_chat_history(self.chat, limit=1):
                if (
                    message.id > self.last
                    and not message.from_user.is_self
                ):
                    self.last = message.id
                    return message
            await asyncio.sleep(0.5)
            timeout -= 0.5

        raise TimeoutError("TimeOut error")

    async def clear_messages(self) -> None:
        """
        Clears the conversation messages.
        """
        async for message in self.client.get_chat_history(self.chat):
            await message.delete()
