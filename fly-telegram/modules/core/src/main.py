#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

"""The core module."""

from time import perf_counter


async def ping_cmd(self):
    """The ping command"""

    start = perf_counter()
    message = await self.message.edit("🏓")

    delay = perf_counter() - start
    emoji = "⚡" if delay < 0.3 else "✨" if delay < 1 else "🐢"

    await message.edit(f"{emoji} <b>Pong! {delay:.3f} ms</b>")
