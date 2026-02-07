#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the CC-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import os
from typing import Union

version = "2.0.0 beta"
logo = r"""
 _______  _____   ___ ___  _______  _______ 
|    ___||     |_|   |   ||_     _||     __|
|    ___||       |\     /   |   |  |    |  |
|___|    |_______| |___|    |___|  |_______|
"""

BASE_DIR = (  # <- from hikka userbot
    "/data"
    if "DOCKER" in os.environ
    else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

SESSION_FILE = os.path.join(
    BASE_DIR,
    "account"
)


async def aioterminal(command: Union[bytes, str]) -> str:
    """
    Async terminal execute
    """
    a = await asyncio.create_subprocess_shell(
        command.strip(),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    out = await a.stdout.read(-1)
    if not out:
        try:
            return (await a.stderr.read(-1)).decode()
        except UnicodeDecodeError:
            return f"Unicode decode error: {(await a.stderr.read(-1))}"
    else:
        try:
            return out.decode()
        except UnicodeDecodeError:
            return f"Unicode decode error: {out}"
