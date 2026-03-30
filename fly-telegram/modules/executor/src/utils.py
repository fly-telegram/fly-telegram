#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html
"""from V1"""

import asyncio

from pyrogram.types import Message
from pyrogram.errors import exceptions


class BufferedStream:
    def __init__(self, stream: asyncio.StreamReader, buffer_size: int):
        """
        Initializes a buffered stream.

        Args:
            stream (asyncio.StreamReader): The stream reader instance.
            buffer_size (int): The buffer size.
        """
        self.stream = stream
        self.buffer = bytearray()
        self.buffer_size = buffer_size

    async def read(self) -> bytes:
        """
        Reads data from the stream.

        Returns:
            bytes: The read data.
        """
        chunk = await self.stream.read(self.buffer_size)
        if not chunk:
            return None

        self.buffer.extend(chunk)
        data = bytes(self.buffer)

        self.buffer.clear()
        return data


class Stream:
    def __init__(
        self,
        stream: asyncio.StreamReader,
        message: Message,
        text: str,
        sleep: int,
        buffer_size: int = 8192,
    ):
        """
        Initializes a stream.

        Args:
            stream (asyncio.StreamReader): The stream reader instance.
            message (Message): The message instance.
            text (str): The text to be processed.
            sleep (int): The sleep time.
            buffer_size (int, optional): The buffer size. Defaults to 8192.
        """
        self.stream = BufferedStream(stream, buffer_size)
        self.message = message
        self.sleep = sleep
        self.text = text
        self.last_chunk = b""

    async def process(self):
        """
        Processes the stream.
        """
        while True:
            chunk = await self.stream.read()
            if chunk:
                if chunk != self.last_chunk:
                    self.last_chunk = chunk
                    self.text += f"<code>{chunk.decode().strip()}</code>\n"
                    try:
                        await self.message.edit(self.text)
                    except (
                        exceptions.bad_request_400.MessageNotModified,
                        exceptions.flood_420.FloodWait,
                    ):
                        pass
                    await asyncio.sleep(self.sleep)
            else:
                break


class AsyncTerminal:
    def __init__(
        self,
        message: Message,
        command: str,
        text: str,
        sleep: int,
        buffer_size: int = 4096,
    ):
        """
        Initializes an async terminal.

        Args:
            message (Message): The message instance.
            command (str): The command to be executed.
            text (str): The text to be processed.
            sleep (int): The sleep time.
            buffer_size (int, optional): The buffer size. Defaults to 4096.
        """
        self.command = command
        self.message = message
        self.text = text
        self.sleep = sleep
        self.buffer_size = buffer_size

    async def run(self) -> int:
        """
        Runs the async terminal.

        Returns:
            int: The exit code.
        """
        process = await asyncio.create_subprocess_shell(
            self.command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout_processor = Stream(
            process.stdout, self.message, self.text, self.sleep, self.buffer_size
        )
        stderr_processor = Stream(
            process.stderr, self.message, self.text, self.sleep, self.buffer_size
        )

        await asyncio.gather(stdout_processor.process(), stderr_processor.process())

        code = await process.wait()
        return code
