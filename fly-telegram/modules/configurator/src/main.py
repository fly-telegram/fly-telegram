import ast
from uuid import uuid4

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from languages import getlang
from loader import Loader

from .utils import get, get_modules, set

loader = Loader()


def _via(call):
    return call.client.inline.viamanager


def _kb(call, buttons):
    via = _via(call)
    rows = []
    for row in buttons:
        line = []
        for b in row:
            if "switch_inline_query_current_chat" in b:
                line.append(
                    InlineKeyboardButton(
                        text=b["text"], switch_inline_query_current_chat=b["switch_inline_query_current_chat"]
                    )
                )
                continue
            if "switch_inline_query" in b:
                line.append(InlineKeyboardButton(text=b["text"], switch_inline_query=b["switch_inline_query"]))
                continue
            cb = b.get("callback")
            params = b.get("params", {})
            if callable(cb):
                uid = str(uuid4())
                via.handlers[uid] = {"callback": cb, "params": params}
                line.append(InlineKeyboardButton(text=b["text"], callback_data=uid))
            else:
                line.append(InlineKeyboardButton(text=b["text"], callback_data=b["callback"]))
        rows.append(line)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_btn(client, module, key, vtype, cur="", lang=None):
    uid = str(uuid4())
    client.inline.viamanager.handlers[f"cfg_{uid}"] = {"module": module, "key": key, "vtype": vtype}
    if lang is None:
        lang = getlang("configurator")
    return {"text": lang.get("enter_new_value"), "switch_inline_query_current_chat": f"cfg_{uid} {cur}"}


def get_choices(module, key):
    from pathlib import Path

    src_path = Path(__file__).parent.parent / module / "src"
    for f in src_path.glob("*.py"):
        try:
            source = f.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ConfigValue":
                    if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == key:
                        for kw in node.keywords:
                            if kw.arg == "validator" and isinstance(kw.value, ast.Call):
                                if isinstance(kw.value.func, ast.Name) and kw.value.func.id == "Choice":
                                    if kw.value.args and isinstance(kw.value.args[0], ast.List):
                                        return [
                                            elt.value for elt in kw.value.args[0].elts if isinstance(elt, ast.Constant)
                                        ]
        except Exception:
            pass
    return []


def convert(value, vtype):
    if vtype == "bool":
        return value.lower() in ("true", "1", "yes", "on") if isinstance(value, str) else bool(value)
    if vtype == "int":
        return int(value)
    if vtype == "float":
        return float(value)
    return value


async def config_cmd(self):
    await self.message.delete()
    modules = get_modules()
    if not modules:
        await self.client.inline.say(self.client, self.message, self.lang.get("no_config"))
        return

    buttons = [
        [{"text": self.lang.get("module_keys").format(name=m["name"], count=len(m["keys"])), "callback": get_module, "params": {"module": m["name"]}}]
        for m in modules
    ]
    buttons.append([{"text": self.lang.get("close"), "callback": close}])

    await self.client.inline.say(self.client, self.message, self.lang.get("configurator_title"), buttons=buttons)


async def get_module(call, module):
    modules = get_modules()
    mod = next((m for m in modules if m["name"] == module), None)
    if not mod:
        await call.answer(call.lang.get("module_not_found"), show_alert=True)
        return

    buttons = []
    for k in mod["keys"]:
        get(module, k["name"], k["default"])
        buttons.append(
            [
                {
                    "text": f"{k['name']}",
                    "callback": edit_key,
                    "params": {
                        "module": module,
                        "key": k["name"],
                        "vtype": k.get("type", "str"),
                        "default": str(k["default"]) if k["default"] is not None else "",
                    },
                }
            ]
        )
    buttons.append([{"text": call.lang.get("back"), "callback": config_cmd}])
    buttons.append([{"text": call.lang.get("close"), "callback": close}])

    await call.edit_message(call.lang.get("module_title").format(module=module), reply_markup=_kb(call, buttons))


async def edit_key(call, module, key, vtype, default):
    cur = get(module, key)
    display = cur if cur is not None else "<i>none</i>"
    buttons = []

    if vtype == "bool":
        new_val = "False" if cur else "True"
        buttons.append(
            [
                {
                    "text": call.lang.get("enable") if not cur else call.lang.get("disable"),
                    "callback": apply,
                    "params": {"module": module, "key": key, "value": new_val, "vtype": vtype},
                }
            ]
        )
    elif vtype == "choice":
        choices = get_choices(module, key)
        for choice in choices:
            prefix = "✅" if choice == cur else "⬜"
            buttons.append(
                [
                    {
                        "text": f"{prefix} {choice}",
                        "callback": apply,
                        "params": {"module": module, "key": key, "value": choice, "vtype": vtype},
                    }
                ]
            )
    else:
        buttons.append([edit_btn(call.client, module, key, vtype, str(cur) if cur else "", lang=call.lang)])

    if default:
        buttons.append(
            [
                {
                    "text": call.lang.get("reset_default"),
                    "callback": apply,
                    "params": {"module": module, "key": key, "value": default, "vtype": vtype},
                }
            ]
        )

    buttons.append([{"text": call.lang.get("back"), "callback": get_module, "params": {"module": module}}])
    buttons.append([{"text": call.lang.get("close"), "callback": close}])

    text = call.lang.get("key_info").format(module=module, key=key, display=display, default=default, vtype=vtype)
    await call.edit_message(text, reply_markup=_kb(call, buttons))


async def apply(call, module, key, value, vtype="str"):
    value = convert(value, vtype)
    set(module, key, value)
    await call.answer(f"✅ {key} = {value}")
    await edit_key(call, module, key, vtype, value)


async def close(call):
    await call.edit_message(call.lang.get("configurator_closed"))


async def _inline_query(client):
    inline = client.inline

    @inline.query()
    async def config_handler(query: InlineQuery):
        q = query.query.strip()

        if not q.startswith("cfg"):
            return None

        lang = getattr(query, "lang", None) or getlang("configurator")
        parts = q.split(maxsplit=1)
        onepart = parts[0]

        if onepart.startswith("cfg_") and len(onepart) > 4:
            uid = onepart  # cfg_<uuid>
            new_val = parts[1] if len(parts) > 1 else ""

            edit_data = inline.viamanager.handlers.get(uid)
            if edit_data and "module" in edit_data:
                module_name = edit_data["module"]
                key = edit_data["key"]
                vtype = edit_data.get("vtype", "str")

                converted = convert(new_val, vtype)
                set(module_name, key, converted)

                await query.answer(
                    results=[
                        InlineQueryResultArticle(
                            id=f"saved_{uid}",
                            title=lang.get("saved"),
                            description=f"{module_name}.{key} = {converted}",
                            input_message_content=InputTextMessageContent(
                                message_text=lang.get("saved_text").format(
                                    module_name=module_name, key=key, converted=converted
                                ),
                                parse_mode="HTML",
                            ),
                        )
                    ],
                    cache_time=0,
                    is_personal=True,
                )
                return True
            else:
                await query.answer(
                    results=[
                        InlineQueryResultArticle(
                            id="expired",
                            title=lang.get("handler_expired_title"),
                            description=lang.get("handler_expired_desc"),
                            input_message_content=InputTextMessageContent(
                                message_text=lang.get("handler_expired_text"), parse_mode="HTML"
                            ),
                        )
                    ],
                    cache_time=0,
                    is_personal=True,
                )
                return True

        parts = q.split(maxsplit=2)
        if len(parts) < 2:
            modules = get_modules()
            if not modules:
                await query.answer(
                    results=[
                        InlineQueryResultArticle(
                            id="no_modules",
                            title=lang.get("no_modules"),
                            description=lang.get("no_configurable"),
                            input_message_content=InputTextMessageContent(
                                message_text=lang.get("no_configurable_text"), parse_mode="HTML"
                            ),
                        )
                    ],
                    cache_time=60,
                    is_personal=True,
                )
                return True

            results = []
            for m in modules:
                results.append(
                    InlineQueryResultArticle(
                        id=f"mod_{m['name']}",
                        title=f"📦 {m['name']}",
                        description=lang.get("configurable_keys").format(count=len(m["keys"])),
                        input_message_content=InputTextMessageContent(
                            message_text=(
                                lang.get("configurator_module_title").format(name=m["name"])
                                + "\n\n"
                                + lang.get("keys_header")
                                + "\n"
                                + "\n".join(f"• <code>{k['name']}</code> ({k.get('type', 'str')})" for k in m["keys"])
                            ),
                            parse_mode="HTML",
                        ),
                    )
                )

            await query.answer(results=results, cache_time=60, is_personal=True)
            return True

        module_name = parts[1]
        modules = get_modules()
        mod = next((m for m in modules if m["name"] == module_name), None)

        if not mod:
            await query.answer(
                results=[
                    InlineQueryResultArticle(
                        id="mod_not_found",
                        title=lang.get("module_not_found_title"),
                        description=lang.get("module_not_found_desc").format(module_name=module_name),
                        input_message_content=InputTextMessageContent(
                            message_text=lang.get("module_not_found_text").format(module_name=module_name), parse_mode="HTML"
                        ),
                    )
                ],
                cache_time=60,
                is_personal=True,
            )
            return True

        if len(parts) < 3:
            results = []
            for k in mod["keys"]:
                cur_val = get(module_name, k["name"], k["default"])
                results.append(
                    InlineQueryResultArticle(
                        id=f"key_{module_name}_{k['name']}",
                        title=f"🔧 {k['name']}",
                        description=lang.get("current_value").format(cur_val=cur_val, vtype=k.get("type", "str")),
                        input_message_content=InputTextMessageContent(
                            message_text=lang.get("key_info_inline").format(
                                module_name=module_name,
                                key_name=k["name"],
                                cur_val=cur_val,
                                default=k["default"],
                                vtype=k.get("type", "str"),
                            ),
                            parse_mode="HTML",
                        ),
                    )
                )

            await query.answer(results=results, cache_time=60, is_personal=True)
            return True

        key_name = parts[2]
        key_info = next((k for k in mod["keys"] if k["name"] == key_name), None)

        if not key_info:
            await query.answer(
                results=[
                    InlineQueryResultArticle(
                        id="key_not_found",
                        title=lang.get("key_not_found"),
                        description=lang.get("key_not_found_desc").format(key_name=key_name, module_name=module_name),
                        input_message_content=InputTextMessageContent(
                            message_text=lang.get("key_not_found_text").format(key_name=key_name, module_name=module_name),
                            parse_mode="HTML",
                        ),
                    )
                ],
                cache_time=60,
                is_personal=True,
            )
            return True

        cur_val = get(module_name, key_name, key_info["default"])
        await query.answer(
            results=[
                InlineQueryResultArticle(
                    id=f"edit_{module_name}_{key_name}",
                    title=lang.get("edit_key_title").format(module_name=module_name, key_name=key_name),
                    description=lang.get("current").format(cur_val=cur_val),
                    input_message_content=InputTextMessageContent(
                        message_text=lang.get("key_info_inline").format(
                            module_name=module_name,
                            key_name=key_name,
                            cur_val=cur_val,
                            default=key_info["default"],
                            vtype=key_info.get("type", "str"),
                        ),
                        parse_mode="HTML",
                    ),
                )
            ],
            cache_time=60,
            is_personal=True,
        )
        return True


@loader.events.on_load
async def _on_load(client):
    await _inline_query(client)
