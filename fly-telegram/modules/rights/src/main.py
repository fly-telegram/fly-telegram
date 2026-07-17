#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from database import database
from languages import getlang
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
        lang = getattr(query, "lang", None) or getlang("rights")
        if not q.startswith("newrights"):
            return None
        parts = q.split(maxsplit=2)
        if len(parts) < 3:
            await query.answer(
                results=[
                    genresult(
                        lang.get("rights_title"),
                        lang.get("invalid_usage"),
                        lang.get("input_user"),
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
                            lang.get("rights_title"),
                            lang.get("user_invalid").format(user=user),
                            lang.get("user_not_found").format(user=user),
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
                        lang.get("rights_title"),
                        lang.get("command_invalid").format(command=command),
                        lang.get("command_not_found").format(command=command),
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
                    title=lang.get("rights_title"),
                    description=lang.get("user_can_use").format(display=display, detail=detail),
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"🕊 <b>{mod}</b>\n\n"
                            f"├─ <i>user</i>: <code>{display}</code>\n"
                            f"└─ <i>access</i>: <code>{detail}</code>\n"
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
    lang = self.lang
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
                                    "text": lang.get("inline_access"),
                                    "callback": get_users,
                                    "params": {"uid": id_},
                                }
                            ]
                        )
                    else:
                        btns.append(
                            [
                                {
                                    "text": lang.get("cmd_inline").format(cmd=cmd, reg=reg.get(cmd, "?")),
                                    "callback": remove,
                                    "params": {"uid": id_, "right": cmd},
                                }
                            ]
                        )
            else:
                btns.append([{"text": lang.get("no_rights"), "callback": close}])
            btns.append([{"text": lang.get("back"), "callback": rights_cmd}])
            btns.append([{"text": lang.get("close"), "callback": close}])
            text = lang.get("user_info").format(name=name, id=id_, count=len(rights))
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
                lang.get("user_not_found_text").format(user=user),
            )
        return
    reg = getattr(self.client.loader, "commands_reg", {})
    if not reg:
        if hasattr(self, "edit_message"):
            await self.edit_message(lang.get("no_commands"))
        else:
            await self.client.inline.say(
                self.client,
                self.message if hasattr(self, "message") else None,
                lang.get("no_commands"),
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
                    "text": lang.get("module_cmd").format(mod=mod, count=len(cmds)),
                    "callback": show_module,
                    "params": {"module": mod},
                }
            ]
        )
    ic = len(users("inline"))
    btns.append([{"text": lang.get("inline_access_count").format(count=ic), "callback": get_users}])
    btns.append([{"text": lang.get("close"), "callback": close}])
    if hasattr(self, "edit_message"):
        await self.edit_message(lang.get("rights_title_text") + "\n", reply_markup=_kb(self, btns))
    else:
        await self.client.inline.say(
            self.client,
            self.message if hasattr(self, "message") else None,
            lang.get("rights_title_text"),
            buttons=btns,
        )


async def show_module(call, module):
    reg = getattr(call.client.loader, "commands_reg", {})
    lang = call.lang
    cmds = sorted(cmd for cmd, mod in reg.items() if mod == module)
    if not cmds:
        await call.answer(lang.get("module_not_found"), show_alert=True)
        return
    data = database.get("rights") or {}
    btns = [
        {
            "text": lang.get("module_cmd_users").format(cmd=cmd, count=sum(1 for uid, cmds_ in data.items() if cmd in cmds_)),
            "callback": show_command,
            "params": {"module": module, "command": cmd},
        }
        for cmd in cmds
    ]
    btns = [[b] for b in btns]
    btns.append([{"text": lang.get("back"), "callback": rights_cmd}])
    btns.append([{"text": lang.get("close"), "callback": close}])
    await call.edit_message(lang.get("module_title").format(module=module), reply_markup=_kb(call, btns))


async def show_command(call, module, command):
    usrs = users(command)
    lang = call.lang
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
                "text": lang.get("add_user"),
                "switch_inline_query_current_chat": f"newrights {command} ",
            }
        ]
    )
    if usrs:
        btns.append(
            [
                {
                    "text": lang.get("revoke_all"),
                    "callback": revoke,
                    "params": {"right": command, "module": module},
                }
            ]
        )
    btns.append([{"text": lang.get("back"), "callback": show_module, "params": {"module": module}}])
    btns.append([{"text": lang.get("close"), "callback": close}])
    text = lang.get("command_info").format(command=command, module=module, count=len(usrs))
    await call.edit_message(text, reply_markup=_kb(call, btns))


async def remove(call, uid, right, module=None):
    lang = call.lang
    btns = [
        [
            {
                "text": lang.get("yes_remove"),
                "callback": remove_user,
                "params": {"uid": uid, "right": right, "module": module},
            }
        ],
        [
            {
                "text": lang.get("no"),
                "callback": show_command,
                "params": {"module": module, "command": right},
            }
        ],
    ]
    await call.edit_message(
        lang.get("remove_rights_text").format(uid=uid, right=right),
        reply_markup=_kb(call, btns),
    )


async def remove_user(call, uid, right, module=None):
    lang = call.lang
    ok = drop(right, uid)
    await call.answer(lang.get("removed") if ok else lang.get("no_rights_for_command"))
    if right == "inline":
        await get_users(call)
    else:
        await show_command(call, module, right)


async def revoke(call, right, module=None):
    lang = call.lang
    ok = drop(right)
    await call.answer(lang.get("revoked").format(right=right) if ok else lang.get("no_users_had_rights"))
    if right == "inline":
        await get_users(call)
    else:
        await show_command(call, module, right)


async def get_users(call):
    usrs = users("inline")
    lang = call.lang
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
                "text": lang.get("add_user"),
                "switch_inline_query_current_chat": "newrights inline ",
            }
        ]
    )
    if usrs:
        btns.append(
            [
                {
                    "text": lang.get("revoke_all"),
                    "callback": revoke,
                    "params": {"right": "inline"},
                }
            ]
        )
    btns.append([{"text": lang.get("back"), "callback": rights_cmd}])
    btns.append([{"text": lang.get("close"), "callback": close}])
    text = lang.get("inline_access_granted").format(count=len(usrs))
    await call.edit_message(text, reply_markup=_kb(call, btns))


async def close(call):
    await call.edit_message(call.lang.get("rights_closed"))


@events.on_load
async def on_load(client):
    await _inline_query(client)
