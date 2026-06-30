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
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import requests

try:
    import ujson as json
except ModuleNotFoundError:
    import json

from loader import Loader

loader = Loader()


try:
    import ujson as json
except ModuleNotFoundError:
    import json


loader = Loader()


def get_files(user, repo, path, branch, prefix=""):
    url = f"https://api.github.com/repos/{user}/{repo}/contents/{path}?ref={branch}"
    files = []

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, dict):
        data = [data]

    for item in data:
        if item["type"] == "dir":
            sub_files = get_files(user, repo, item["path"], branch, prefix + item["name"] + "/")
            files.extend(sub_files)
        else:
            files.append({"path": prefix + item["name"], "url": item["download_url"]})
    return files


@loader.alias("dlm")
async def dload_cmd(self, link: str):
    """.dlm https://github.com/fly-telegram/modules/tree/main/community/module/"""
    pattern = r"github\.com/([^/]+)/([^/]+)/(?:blob|tree)/([^/]+)(?:/(.*))?"
    match = re.search(pattern, link)

    if not match:
        await self.message.edit("❌ <b>Not a valid GitHub link!</b>")
        return

    username = match[1]
    repo = match[2]
    branch = match[3]
    path = match[4]

    module_name = path.strip("/").split("/")[-1] if path else repo

    message = await self.message.edit(f"🕊 <b>{module_name}</b>\n<code>Fetching file list from GitHub...</code>")

    try:
        files = get_files(username, repo, path, branch)
        if not files:
            await message.edit("❌ <b>No files or module invalid!</b>")
            return
    except Exception as error:
        await message.edit(f"❌ <b>Failed to fetch files from GitHub!</b>\n<code>{error}</code>")
        return
    modules_path = Path(__file__).parent.parent.parent
    module_dir = modules_path / module_name

    if module_dir.exists():
        await message.edit(f"🕊 <b>{module_name}</b>\n<code>Module already exists. Overwriting...</code>")
        shutil.rmtree(module_dir)

    module_dir.mkdir(parents=True, exist_ok=True)

    await message.edit(f"🕊 <b>{module_name}</b>\n<code>Downloading {len(files)} files...</code>")

    for file in files:
        filepath = file["path"]
        full = module_dir / filepath
        full.parent.mkdir(parents=True, exist_ok=True)

        try:
            response = requests.get(file["url"])
            response.raise_for_status()
            with open(full, "wb") as f:
                f.write(response.content)
        except Exception as error:
            await message.edit(f"❌ <b>Failed to download {filepath}!</b>\n<code>{error}</code>")
            return

    meta_path = module_dir / "meta.json"

    with open(meta_path) as file:
        meta = json.load(file)

    name = meta.get("name", module_name)
    if deps := meta.get("deps", None):
        formatted = "\n".join(
            f"├─ {requirement}" if i < len(deps) - 1 else f"└─ {requirement}" for i, requirement in enumerate(deps)
        )
        await message.edit(f"🕊 <b>{name}</b>\n<code>Installing required libs...</code>\n{formatted}")
        pip = await asyncio.create_subprocess_exec(sys.executable, "-m", "pip", "install", "-q", *deps)
        output = await pip.wait()

        if output != 0:
            await self.message.edit(f"❌ <b>{name} installing error</b>\n<code>Failed to install libs.</code>")
            shutil.rmtree(module_dir)
            return

    await message.edit(f"🕊 <b>{name}</b>\n<code>Loading module...</code>")

    try:
        await loader.load(module_name, self.client, startup=True)
    except Exception as error:
        await self.message.edit(f"❌ <b>{name} installing error</b>\n<code>{error}</code>")

        shutil.rmtree(module_dir)
        return

    await message.edit(f"🕊 <b>{name} is loaded!</b>")


@loader.alias("lm")
async def load_cmd(self, flags: str):
    splitted_flags = flags.split()  # .lm no-delete

    reply = self.message.reply_to_message
    file = self.message if self.message.document else reply if reply and reply.document else None

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

    message = await self.message.edit(f"🕊 <b>{module_name}</b>\n<code>Downloading module...</code>")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, filename)
        await file.download(temp_path)

        await message.edit(f"🕊 <b>{module_name}</b>\n<code>Extracting module...</code>")

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
    if deps := meta.get("deps", None):
        formatted = "\n".join(
            f"├─ {requirement}" if i < len(deps) - 1 else f"└─ {requirement}" for i, requirement in enumerate(deps)
        )
        await message.edit(f"🕊 <b>{name}</b>\n<code>Installing required libs...</code>\n{formatted}")
        pip = await asyncio.create_subprocess_exec(sys.executable, "-m", "pip", "install", "-q", *deps)
        output = await pip.wait()

        if output != 0:
            await self.message.edit(f"❌ <b>{name} installing error</b>\n<code>Failed to install libs.</code>")

            if "no-delete" not in splitted_flags:
                shutil.rmtree(os.path.join(modules_path, module_name))
            return

    await message.edit(f"🕊 <b>{name}</b>\n<code>Loading module...</code>")

    try:
        await loader.load(module_name, self.client, startup=True)
    except Exception as error:
        await self.message.edit(f"❌ <b>{name} installing error</b>\n<code>{error}</code>")

        if "no-delete" not in splitted_flags:
            shutil.rmtree(os.path.join(modules_path, module_name))
        return

    await message.edit(f"🕊 <b>{name} is loaded!</b>")


@loader.alias("unlm")
async def unload_cmd(self, name: str):
    # fly-telegram/fly-telegram/modules
    modules_path = Path(__file__).parent.parent.parent

    message = await self.message.edit(f"🕊 <b>{name}</b>\n<code>Removing module...</code>")

    try:
        await loader.unload(name, self.client)
    except Exception as error:
        await self.message.edit(f"❌ <b>{name} unloading error</b>\n<code>{error}</code>")
        return

    shutil.rmtree(os.path.join(modules_path, name))

    await message.edit(f"🕊 <b>{name} unloaded!</b>")
