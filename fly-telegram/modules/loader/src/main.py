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
        await self.message.edit(self.lang.get("invalid_github_link"))
        return

    username = match[1]
    repo = match[2]
    branch = match[3]
    path = match[4]

    module_name = path.strip("/").split("/")[-1] if path else repo

    message = await self.message.edit(self.lang.get("fetching_files").format(module_name=module_name))

    try:
        files = get_files(username, repo, path, branch)
        if not files:
            await message.edit(self.lang.get("no_files"))
            return
    except Exception as error:
        await message.edit(self.lang.get("fetch_error").format(error=error))
        return
    modules_path = Path(__file__).parent.parent.parent
    module_dir = modules_path / module_name

    if module_dir.exists():
        await message.edit(self.lang.get("overwriting").format(module_name=module_name))
        shutil.rmtree(module_dir)

    module_dir.mkdir(parents=True, exist_ok=True)

    await message.edit(self.lang.get("downloading_files").format(module_name=module_name, count=len(files)))

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
            await message.edit(self.lang.get("download_error").format(filepath=filepath, error=error))
            return

    meta_path = module_dir / "meta.json"

    with open(meta_path) as file:
        meta = json.load(file)

    name = meta.get("name", module_name)
    if deps := meta.get("deps", None):
        formatted = "\n".join(
            f"├─ <code>{requirement}</code>" if i < len(deps) - 1 else f"└─ <code>{requirement}</code>" for i, requirement in enumerate(deps)
        )
        await message.edit(self.lang.get("installing_deps").format(name=name) + f"\n{formatted}")
        pip = await asyncio.create_subprocess_exec(sys.executable, "-m", "pip", "install", "-q", *deps)
        output = await pip.wait()

        if output != 0:
            await self.message.edit(self.lang.get("install_error").format(name=name))
            shutil.rmtree(module_dir)
            return

    await message.edit(self.lang.get("loading_module").format(name=name))

    try:
        await loader.load(module_name, self.client, startup=True)
    except Exception as error:
        await self.message.edit(self.lang.get("load_error").format(name=name, error=error))

        shutil.rmtree(module_dir)
        return

    await message.edit(self.lang.get("module_loaded").format(name=name))


@loader.alias("lm")
async def load_cmd(self, flags: str):
    splitted_flags = flags.split()  # .lm no-delete

    reply = self.message.reply_to_message
    file = self.message if self.message.document else reply if reply and reply.document else None

    # fly-telegram/fly-telegram/modules
    modules_path = Path(__file__).parent.parent.parent

    if not file:
        await self.message.edit(self.lang.get("reply_needed"))
        return

    filename = file.document.file_name
    module_name = filename.split(".zip")[0]

    if not filename.endswith(".zip"):
        await self.message.edit(self.lang.get("invalid_format"))
        return

    message = await self.message.edit(self.lang.get("downloading_module").format(module_name=module_name))

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, filename)
        await file.download(temp_path)

        await message.edit(self.lang.get("extracting_module").format(module_name=module_name))

        try:
            with zipfile.ZipFile(temp_path, "r") as archive:
                archive.extractall(modules_path / module_name)

        except zipfile.BadZipFile:
            await self.message.edit(self.lang.get("invalid_zip").format(module_name=module_name))
            return

    # meta.json logic
    meta_path = modules_path / module_name / "meta.json"

    with open(meta_path) as file:
        meta = json.load(file)

    name = meta.get("name", module_name)
    if deps := meta.get("deps", None):
        formatted = "\n".join(
            f"├─ <code>{requirement}</code>" if i < len(deps) - 1 else f"└─ <code>{requirement}</code>" for i, requirement in enumerate(deps)
        )
        await message.edit(self.lang.get("installing_deps").format(name=name) + f"\n{formatted}")
        pip = await asyncio.create_subprocess_exec(sys.executable, "-m", "pip", "install", "-q", *deps)
        output = await pip.wait()

        if output != 0:
            await self.message.edit(self.lang.get("install_error").format(name=name))

            if "no-delete" not in splitted_flags:
                shutil.rmtree(os.path.join(modules_path, module_name))
            return

    await message.edit(self.lang.get("loading_module").format(name=name))

    try:
        await loader.load(module_name, self.client, startup=True)
    except Exception as error:
        await self.message.edit(self.lang.get("load_error").format(name=name, error=error))

        if "no-delete" not in splitted_flags:
            shutil.rmtree(os.path.join(modules_path, module_name))
        return

    await message.edit(self.lang.get("module_loaded").format(name=name))


@loader.alias("unlm")
async def unload_cmd(self, name: str):
    # fly-telegram/fly-telegram/modules
    modules_path = Path(__file__).parent.parent.parent

    await self.message.edit(self.lang.get("removing_module").format(name=name))

    try:
        await loader.unload(name, self.client)
    except Exception as error:
        await self.message.edit(self.lang.get("unloading_error").format(name=name, error=error))
        return

    shutil.rmtree(os.path.join(modules_path, name))

    await self.message.edit(self.lang.get("module_unloaded").format(name=name))
