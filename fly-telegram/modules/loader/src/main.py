#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

"""The loader module"""
import asyncio
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from loader import Loader

loader = Loader()

@loader.alias('lm')
async def load_cmd(self, flags: str):
    splitted_flags = flags.split()  # .lm no-delete

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

    # meta.json logic
    meta_path = modules_path / module_name / "meta.json"

    with open(meta_path) as file:
        meta = json.load(file)

    name = meta.get("name", module_name)
    deps = meta.get("deps", None)

    if deps:
        formatted = "\n".join(
            f"├─ {requirement}" if i < len(
                deps) - 1 else f"└─ {requirement}"
            for i, requirement in enumerate(deps)
        )
        await message.edit(
            f"🕊 <b>{name}</b>\n"
            "<code>Installing required libs...</code>\n"
            f"{formatted}"
        )
        pip = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pip", "install", "-q", *deps
        )
        output = await pip.wait()

        if output != 0:
            await self.message.edit(
                f"❌ <b>{name} installing error</b>\n"
                f"<code>Failed to install libs.</code>"
            )

            if "no-delete" not in splitted_flags:
                shutil.rmtree(os.path.join(modules_path, module_name))
            return

    await message.edit(
        f"🕊 <b>{name}</b>\n"
        "<code>Loading module...</code>"
    )

    try:
        await loader.load(module_name, self.client, startup=True)
    except Exception as error:
        await self.message.edit(
            f"❌ <b>{name} installing error</b>\n"
            f"<code>{error}</code>"
        )

        if "no-delete" not in splitted_flags:
            shutil.rmtree(os.path.join(modules_path, module_name))
        return

    await message.edit(
        f"🕊 <b>{name} is loaded!</b>"
    )

@loader.alias('unlm')
async def unload_cmd(self, name: str):
    # fly-telegram/fly-telegram/modules
    modules_path = Path(__file__).parent.parent.parent

    message = await self.message.edit(
        f"🕊 <b>{name}</b>\n"
        "<code>Removing module...</code>"
    )

    try:
        await loader.unload(name, self.client)
    except Exception as error:
        await self.message.edit(
            f"❌ <b>{name} unloading error</b>\n"
            f"<code>{error}</code>"
        )
        return

    shutil.rmtree(os.path.join(modules_path, name))

    await message.edit(
        f"🕊 <b>{name} unloaded!</b>"
    )
