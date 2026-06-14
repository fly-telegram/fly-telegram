#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

import asyncio
from pyrogram import Client, errors
from pyrogram.types import ChatAdministratorRights
from loader import events
from database import database


@events.on_load
async def start(client: Client):
    chats = database.get("chats")
    if not isinstance(chats, dict):
        chats = {}

    ids = []

    for key, title, desc in [
        ("logs", "fly-telegram logs", "Logs channel for fly-telegram"),
        ("backups", "fly-telegram backups", "Backups channel for fly-telegram"),
        ("updates", "fly-telegram updates", "Updates channel for fly-telegram"),
    ]:
        cid = chats.get(key)
        if not cid:
            try:
                channel = await client.create_channel(title=title, description=desc)
                cid = channel.id
                chats[key] = cid
            except errors.FloodWait as e:
                await asyncio.sleep(e.value)
                channel = await client.create_channel(title=title, description=desc)
                cid = channel.id
                chats[key] = cid
            except Exception:
                continue

        ids.append(cid)

    database.set("chats", chats)

    if not ids:
        return

    try:
        folder = None
        for f in await client.get_folders():
            if f.name == "fly-telegram":
                folder = f
                break

        if folder:
            await client.edit_folder(folder.id, included_chats=ids)
        else:
            await client.create_folder(name="fly-telegram", included_chats=ids)
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        if folder:
            await client.edit_folder(folder.id, included_chats=ids)
        else:
            await client.create_folder(name="fly-telegram", included_chats=ids)
    except Exception:
        pass

    try:
        bot = client.inline and client.inline.bot
        if not bot:
            return

        me = await bot.get_me()
        rights = ChatAdministratorRights(
            can_post_messages=True, can_edit_messages=True)
        for cid in ids:
            try:
                await client.promote_chat_member(cid, me.id, privileges=rights)
            except Exception:
                pass
    except Exception:
        pass
