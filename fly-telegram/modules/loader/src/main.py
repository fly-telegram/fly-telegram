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
import aiohttp
import tempfile
import zipfile
import shutil
import sys
import os
try:
    import ujson as json
except ModuleNotFoundError:
    import json

from loader import Loader

loader = Loader()

async def lm_cmd(self):
    reply = self.message.reply_to_message
    file = (
        self.message if self.message.document
        else reply
        if reply and reply.document
        else None
    )

    path = os.path.join("fly-telegram", "modules")

    if not file:
        await self.message.edit("❌ <b>A reply or a document is needed!</b>")
        return
    
    filename = file.document.file_name
    module_name = filename.split(".zip")[0]

    if not filename.endswith(".zip"):
        await self.message.edit("❌ <b>Invalid file format!</b>")
        return
    
    await self.message.edit(
        "🕊 <b>{module_name}</b>\n"
        "<code>Downloading module...</code>"
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, filename)
        await file.download(temp_path)
        
        with zipfile.ZipFile(temp_path, "r") as archive:
            archive.extractall(os.path.join(path, module_name))
    
    try:
        await loader.load(module_name, self.client)
    except Exception as error:
        await self.message.edit(
            f"❌ <b>{module_name} installing error</b>\n"
            f"<code>{error}</code>"
        )
        shutil.rmtree(os.path.join(path, module_name))
        return
    
    await self.message.edit(
        f"🕊 <b>{module_name} is loaded!</b>"
    )
    