#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

"""The loader module"""
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

try:
    import ujson as json
except ModuleNotFoundError:
    pass

from loader import Loader

loader = Loader()

async def lm_cmd(self, flags: str):
    splitted_flags = flags.split() # .lm no-delete

    reply = self.message.reply_to_message
    file = (
        self.message if self.message.document
        else reply
        if reply and reply.document
        else None
    )

    # fly-telegram/fly-telegram/modules
    modules_path = Path(__file__).parent.parent.parent

    if not file:
        await self.message.edit("❌ <b>A reply or a document is needed!</b>")
        return

    filename = file.document.file_name
    module_name = filename.split(".zip")[0]

    if not filename.endswith(".zip"):
        await self.message.edit("❌ <b>Invalid file format!</b>")
        return

    message = await self.message.edit(
        f"🕊 <b>{module_name}</b>\n"
        "<code>Downloading module...</code>"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, filename)
        await file.download(temp_path)

        await message.edit(
            f"🕊 <b>{module_name}</b>\n"
            "<code>Extracting module...</code>"
        )

        try:
            with zipfile.ZipFile(temp_path, "r") as archive:
                archive.extractall(modules_path / module_name)

        except zipfile.BadZipFile:
            await self.message.edit(f"❌ <b>{module_name} is not a valid zip file!</b>")
            return

    await message.edit(
        f"🕊 <b>{module_name}</b>\n"
        "<code>Loading module...</code>"
    )

    try:
        await loader.load(module_name, self.client)
    except Exception as error:
        await self.message.edit(
            f"❌ <b>{module_name} installing error</b>\n"
            f"<code>{error}</code>"
        )

        if not "no-delete" in splitted_flags:
            shutil.rmtree(os.path.join(modules_path, module_name))
        return

    await message.edit(
        f"🕊 <b>{module_name} is loaded!</b>"
    )
