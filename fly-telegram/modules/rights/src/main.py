from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from database import database
from loader import events

from .utils import _kb, genresult


def drop(right, uid=None):
    data = database.get("rights") or {}
    if uid:
        rights = data.get(uid, [])
        if right not in rights:
            return False
        rights.remove(right)
        if rights:
            data[uid] = rights
        else:
            del data[uid]
    else:
        changed = False
        for uid, cmds in list(data.items()):
            if right in cmds:
                cmds.remove(right)
                if cmds:
                    data[uid] = cmds
                else:
                    del data[uid]
                changed = True
        if not changed:
            return False
    database.set("rights", data)
    return True


def users(right):
    data = database.get("rights") or {}
    return sorted(uid for uid, cmds in data.items() if right in cmds)


async def _inline_query(client):
    @client.inline.query()
    async def handler(query: InlineQuery):
        q = query.query.strip()
        if not q.startswith("newrights"):
            return None
        parts = q.split(maxsplit=2)
        if len(parts) < 3:
            await query.answer(
                results=[
                    genresult(
                        "🕊 fly-telegram rights",
                        "❌ Invalid usage",
                        "❌ <b>Input username or user ID</b>",
                    )
                ],
                cache_time=0,
                is_personal=True,
            )
            return True
        command, user = parts[1], parts[2]
        if user.isdigit():
            uid = user
        else:
            try:
                uid = str((await client.get_users(user)).id)
            except Exception:
                await query.answer(
                    results=[
                        genresult(
                            "🕊 fly-telegram rights",
                            f"❌ '{user}' is invalid",
                            f"❌ <b>User '{user}' not found!</b>",
                        )
                    ],
                    cache_time=0,
                    is_personal=True,
                )
                return True
        reg = getattr(client.loader, "commands_reg", {})
        if command not in reg and command != "inline":
            await query.answer(
                results=[
                    genresult(
                        "🕊 fly-telegram rights",
                        f"❌ '.{command}' not found",
                        f"❌ <b>Command '.{command}' not found!</b>",
                    )
                ],
                cache_time=0,
                is_personal=True,
            )
            return True
        data = database.get("rights") or {}
        urights = data.get(uid, [])
        if command not in urights:
            urights.append(command)
        data[uid] = urights
        database.set("rights", data)
        try:
            u = await client.get_users(int(uid))
            display = u.first_name or uid
            if u.last_name:
                display += f" {u.last_name}"
            if u.username:
                display += f" (@{u.username})"
        except Exception:
            display = uid
        detail = "inline bot & via messages" if command == "inline" else f".{command}"
        mod = "inline" if command == "inline" else reg.get(command, "?")
        await query.answer(
            results=[
                InlineQueryResultArticle(
                    id=f"rights_new_{uid}_{command}",
                    title="🕊 fly-telegram rights",
                    description=f"User {display} can now use {detail}",
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"🕊 <b>{mod}</b>\n\n"
                            f"├─ <i>user</i>: <code>{display}</code>\n"
                            f"├─ <i>access</i>: <code>{detail}</code>\n"
                        ),
                        parse_mode="HTML",
                    ),
                )
            ],
            cache_time=0,
            is_personal=True,
        )
        return True


async def rights_cmd(self, user=""):
    if hasattr(self, "message") and self.message:
        await self.message.delete()
    if user:
        try:
            target = await self.client.get_users(user.strip())
            id_ = str(target.id)
            data = database.get("rights") or {}
            rights = data.get(id_, [])
            try:
                u = await self.client.get_users(int(id_))
                name = u.first_name or id_
                if u.last_name:
                    name += f" {u.last_name}"
                if u.username:
                    name += f" (@{u.username})"
            except Exception:
                name = id_
            reg = getattr(self.client.loader, "commands_reg", {})
            btns = []
            if rights:
                for cmd in sorted(rights):
                    if cmd == "inline":
                        btns.append(
                            [
                                {
                                    "text": "🕊️ Inline Access",
                                    "callback": get_users,
                                    "params": {"uid": id_},
                                }
                            ]
                        )
                    else:
                        btns.append(
                            [
                                {
                                    "text": f"🕊 .{cmd} [{reg.get(cmd, '?')}]",
                                    "callback": remove,
                                    "params": {"uid": id_, "right": cmd},
                                }
                            ]
                        )
            else:
                btns.append([{"text": "No rights yet", "callback": close}])
            btns.append([{"text": "⬅️ Back", "callback": rights_cmd}])
            btns.append([{"text": "❌ Close", "callback": close}])
            text = f"👤 <b>{name}</b>\n├─ <i>id</i>: <code>{id_}</code>\n└─ <i>commands</i>: <code>{len(rights)}</code>"
            if hasattr(self, "edit_message"):
                await self.edit_message(text, reply_markup=_kb(self, btns))
            else:
                await self.client.inline.say(
                    self.client,
                    self.message if hasattr(self, "message") else None,
                    text,
                    buttons=btns,
                )
        except Exception:
            await self.client.inline.say(
                self.client,
                self.message if hasattr(self, "message") else None,
                f"❌ <b>User '{user}' not found!</b>",
            )
        return
    reg = getattr(self.client.loader, "commands_reg", {})
    if not reg:
        if hasattr(self, "edit_message"):
            await self.edit_message("❌ <b>No commands found!</b>")
        else:
            await self.client.inline.say(
                self.client,
                self.message if hasattr(self, "message") else None,
                "❌ <b>No commands found!</b>",
            )
        return
    modules = {}
    for cmd, mod in reg.items():
        modules.setdefault(mod, []).append(cmd)
    btns = []
    for mod, cmds in sorted(modules.items()):
        btns.append(
            [
                {
                    "text": f"📦 {mod} ({len(cmds)} cmd)",
                    "callback": show_module,
                    "params": {"module": mod},
                }
            ]
        )
    ic = len(users("inline"))
    btns.append([{"text": f"🕊️ Inline Access ({ic})", "callback": get_users}])
    btns.append([{"text": "❌ Close", "callback": close}])
    if hasattr(self, "edit_message"):
        await self.edit_message("<b>🕊 fly-telegram rights</b>\n", reply_markup=_kb(self, btns))
    else:
        await self.client.inline.say(
            self.client,
            self.message if hasattr(self, "message") else None,
            "<b>🕊 fly-telegram rights</b>",
            buttons=btns,
        )


async def show_module(call, module):
    reg = getattr(call.client.loader, "commands_reg", {})
    cmds = sorted(cmd for cmd, mod in reg.items() if mod == module)
    if not cmds:
        await call.answer("❌ Module not found!", show_alert=True)
        return
    data = database.get("rights") or {}
    btns = [
        {
            "text": f"🔧 .{cmd} ({sum(1 for uid, cmds_ in data.items() if cmd in cmds_)} users)",
            "callback": show_command,
            "params": {"module": module, "command": cmd},
        }
        for cmd in cmds
    ]
    btns = [[b] for b in btns]
    btns.append([{"text": "⬅️ Back", "callback": rights_cmd}])
    btns.append([{"text": "❌ Close", "callback": close}])
    await call.edit_message(f"🕊 <b>{module}</b>", reply_markup=_kb(call, btns))


async def show_command(call, module, command):
    usrs = users(command)
    btns = [
        {
            "text": f"👤 {uid}",
            "callback": remove,
            "params": {"uid": uid, "right": command, "module": module},
        }
        for uid in usrs
    ]
    btns = [[b] for b in btns]
    btns.append(
        [
            {
                "text": "➕ Add user",
                "switch_inline_query_current_chat": f"newrights {command} ",
            }
        ]
    )
    if usrs:
        btns.append(
            [
                {
                    "text": "🔄 Revoke all",
                    "callback": revoke,
                    "params": {"right": command, "module": module},
                }
            ]
        )
    btns.append([{"text": "⬅️ Back", "callback": show_module, "params": {"module": module}}])
    btns.append([{"text": "❌ Close", "callback": close}])
    text = f"🕊 <b>.{command}</b>\n├─ <i>module</i>: <code>{module}</code>\n└─ <i>users with rights</i>: <code>{len(usrs)}</code>"
    await call.edit_message(text, reply_markup=_kb(call, btns))


async def remove(call, uid, right, module=None):
    btns = [
        [
            {
                "text": "✅ Yes, remove",
                "callback": remove_user,
                "params": {"uid": uid, "right": right, "module": module},
            }
        ],
        [
            {
                "text": "❌ No",
                "callback": show_command,
                "params": {"module": module, "command": right},
            }
        ],
    ]
    await call.edit_message(
        f"🕊 <b>Remove rights</b>\nRemove <code>{uid}</code>'s right to use <code>.{right}</code>?",
        reply_markup=_kb(call, btns),
    )


async def remove_user(call, uid, right, module=None):
    ok = drop(right, uid)
    await call.answer("✅ Removed!" if ok else "❌ No rights for this command.")
    if right == "inline":
        await get_users(call)
    else:
        await show_command(call, module, right)


async def revoke(call, right, module=None):
    ok = drop(right)
    await call.answer(f"✅ Revoked .{right} for all!" if ok else "❌ No users had rights.")
    if right == "inline":
        await get_users(call)
    else:
        await show_command(call, module, right)


async def get_users(call):
    usrs = users("inline")
    btns = [
        {
            "text": f"👤 {uid}",
            "callback": remove,
            "params": {"uid": uid, "right": "inline"},
        }
        for uid in usrs
    ]
    btns = [[b] for b in btns]
    btns.append(
        [
            {
                "text": "➕ Add user",
                "switch_inline_query_current_chat": "newrights inline ",
            }
        ]
    )
    if usrs:
        btns.append(
            [
                {
                    "text": "🔄 Revoke all",
                    "callback": revoke,
                    "params": {"right": "inline"},
                }
            ]
        )
    btns.append([{"text": "⬅️ Back", "callback": rights_cmd}])
    btns.append([{"text": "❌ Close", "callback": close}])
    text = f"🕊️ <b>Inline Access</b>\n└─ <i>granted</i>: <code>{len(usrs)}</code>"
    await call.edit_message(text, reply_markup=_kb(call, btns))


async def close(call):
    await call.edit_message("🕊 <b>Rights closed</b>")


@events.on_load
async def on_load(client):
    await _inline_query(client)
