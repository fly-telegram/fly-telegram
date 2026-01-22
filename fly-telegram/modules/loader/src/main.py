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
    """The loader module command"""
    reply = self.message.reply_to_message
    file = (
        self.message if self.message.document
        else reply
        if reply and reply.document
        else None
    )

    path = loader.modules_path

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

    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, filename)
    
    try:
        await file.download(temp_path)
        
        await message.edit(
            f"🕊 <b>{module_name}</b>\n"
            "<code>Extracting module...</code>"
        )
        
        module_path = path / module_name
        
        if module_path.exists():
            def rmexists():
                shutil.rmtree(module_path, ignore_errors=True)
            await asyncio.to_thread(rmexists)
        
        def extract():
            try:
                with zipfile.ZipFile(temp_path, "r") as archive:
                    archive.extractall(module_path)
                return True, None
            except zipfile.BadZipFile as e:
                return False, f"{module_name} is not a valid zip file!"
            except Exception as e:
                return False, str(e)
        
        ex_result, ex_error = await asyncio.to_thread(extract)
        
        if not ex_result:
            await message.edit(f"❌ <b>{ex_error}</b>")
            return
        
        await message.edit(
            f"🕊 <b>{module_name}</b>\n"
            "<code>Installing module...</code>"
        )
        
        try:
            await loader.load(module_name, self.client)
        except Exception as error:
            await message.edit(
                f"❌ <b>{module_name} installing error</b>\n"
                f"<code>{error}</code>"
            )
            def rm_mod():
                if module_path.exists():
                    shutil.rmtree(module_path, ignore_errors=True)
            await asyncio.to_thread(rm_mod)
            return
        
        await message.edit(
            f"🕊 <b>{module_name} is loaded!</b>"
        )
        
    except Exception as error:
        await message.edit(
            f"❌ <b>Unexpected error:</b>\n"
            f"<code>{error}</code>"
        )
    finally:
        def clean():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass
        
        await asyncio.to_thread(clean)