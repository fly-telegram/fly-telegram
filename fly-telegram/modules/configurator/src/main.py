import ast
from pathlib import Path
from uuid import uuid4
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent
)
from loader import Loader
from .utils import get_modules, get, set

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
                line.append(InlineKeyboardButton(
                    text=b["text"],
                    switch_inline_query_current_chat=b["switch_inline_query_current_chat"])
                )
                continue
            if "switch_inline_query" in b:
                line.append(InlineKeyboardButton(
                    text=b["text"],
                    switch_inline_query=b["switch_inline_query"])
                )
                continue
            cb = b.get("callback")
            params = b.get("params", {})
            if callable(cb):
                uid = str(uuid4())
                via.handlers[uid] = {"callback": cb, "params": params}
                line.append(InlineKeyboardButton(
                    text=b["text"], callback_data=uid))
            else:
                line.append(InlineKeyboardButton(
                    text=b["text"], callback_data=b["callback"]))
        rows.append(line)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_btn(client, module, key, vtype, cur=""):
    uid = str(uuid4())
    client.inline.viamanager.handlers[f"cfg_{uid}"] = {
        "module": module,
        "key": key,
        "vtype": vtype
    }
    return {"text": "✏️ Enter new value", "switch_inline_query_current_chat": f"cfg_{uid} {cur}"}


def get_choices(module, key):
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
                                        return [elt.value for elt in kw.value.args[0].elts if isinstance(elt, ast.Constant)]
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
        await self.client.inline.say(
            self.client, self.message,
            "❌ <b>No config in modules found!</b>"
        )
        return

    buttons = [
        [{"text": f"📦 {m['name']} ({len(m['keys'])} keys)",
          "callback": get_module,
          "params": {
              "module": m["name"]}
          }] for m in modules]
    buttons.append([{"text": "❌ Close", "callback": close}])

    await self.client.inline.say(
        self.client, self.message,
        "🕊 <b>Configurator</b>",
        buttons=buttons
    )


async def get_module(call, module):
    modules = get_modules()
    mod = next((m for m in modules if m["name"] == module), None)
    if not mod:
        await call.answer("❌ Module not found!", show_alert=True)
        return

    buttons = []
    for k in mod["keys"]:
        get(module, k["name"], k["default"])
        buttons.append([
            {"text": f"{k['name']}",
             "callback": edit_key,
             "params": {
                 "module": module,
                 "key": k["name"],
                 "vtype": k.get("type", "str"),
                 "default": str(k["default"])
                 if k["default"] is not None else ""
             }
             }])
    buttons.append([{"text": "⬅️ Back", "callback": config_cmd}])
    buttons.append([{"text": "❌ Close", "callback": close}])

    await call.edit_message(
        f"🕊 <b>{module}</b>",
        reply_markup=_kb(call, buttons)
    )


async def edit_key(call, module, key, vtype, default):
    cur = get(module, key)
    display = cur if cur is not None else "<i>none</i>"
    buttons = []

    if vtype == "bool":
        new_val = "False" if cur else "True"
        buttons.append(
            [{
                "text": "✅ Enable" if not cur else "❌ Disable",
                "callback": apply,
                "params": {
                    "module": module,
                    "key": key,
                    "value": new_val,
                    "vtype": vtype
                }}
             ])
    elif vtype == "choice":
        choices = get_choices(module, key)
        for choice in choices:
            prefix = "✅" if choice == cur else "⬜"
            buttons.append([
                {
                    "text": f"{prefix} {choice}",
                    "callback": apply,
                    "params": {
                        "module": module,
                        "key": key,
                        "value": choice,
                        "vtype": vtype
                    }
                }])
    else:
        buttons.append(
            [edit_btn(call.client, module, key, vtype, str(cur) if cur else "")])

    if default:
        buttons.append([{
            "text": "🔄 Reset to default",
            "callback": apply,
            "params": {
                "module": module,
                "key": key,
                "value": default,
                "vtype": vtype
            }
        }])

    buttons.append(
        [{
            "text": "⬅️ Back",
            "callback": get_module,
            "params": {"module": module}
        }])
    buttons.append([{"text": "❌ Close", "callback": close}])

    text = (
        f"🕊 <b>{module}</b>\n"
        f"├─ <i>key</i>: <code>{key}</code>\n"
        f"├─ <i>value</i>: <code>{display}</code> (<i>default</i>: <code>{default}</code>)\n"
        f"└─ <i>type</i>: <code>{vtype}</code>\n"
    )
    await call.edit_message(text, reply_markup=_kb(call, buttons))


async def apply(call, module, key, value, vtype="str"):
    value = convert(value, vtype)
    set(module, key, value)
    await call.answer(f"✅ {key} = {value}")
    await edit_key(call, module, key, vtype, value)


async def close(call):
    await call.edit_message("🕊 <b>Configurator closed</b>")


# Inline query handler for quick config access
async def _register_inline_query(client):
    """Register inline query handler via decorator"""
    inline = client.inline

    @inline.query()
    async def config_inline_handler(query: InlineQuery):
        """Handle 'cfg' inline query for quick config access"""
        q = query.query.strip()

        if not q.startswith("cfg"):
            return None

        # Check if this is a config edit request: cfg_<uuid> <value>
        # Format: cfg_<uuid> <new_value> - save value to config
        parts = q.split(maxsplit=1)
        first_part = parts[0]

        # If first part is cfg_<uuid> (has underscore after cfg), it's a save request
        if first_part.startswith("cfg_") and len(first_part) > 4:
            uid = first_part  # cfg_<uuid>
            new_val = parts[1] if len(parts) > 1 else ""

            # Find handler data in viamanager
            edit_data = inline.viamanager.handlers.get(uid)
            if edit_data and "module" in edit_data:
                module_name = edit_data["module"]
                key = edit_data["key"]
                vtype = edit_data.get("vtype", "str")

                # Convert and save value
                converted = convert(new_val, vtype)
                set(module_name, key, converted)

                await query.answer(results=[
                    InlineQueryResultArticle(
                        id=f"saved_{uid}",
                        title="✅ Saved!",
                        description=f"{module_name}.{key} = {converted}",
                        input_message_content=InputTextMessageContent(
                            message_text=(
                                "✅ <b>Saved!</b>\n\n"
                                f"├─ <i>module</i>: <code>{module_name}</code>\n"
                                f"├─ <i>key</i>: <code>{key}</code>\n"
                                f"└─ <i>value</i>: <code>{converted}</code>"
                            ),
                            parse_mode="HTML"
                        )
                    )
                ], cache_time=0, is_personal=True)
                return True
            else:
                await query.answer(results=[
                    InlineQueryResultArticle(
                        id="expired",
                        title="⚠️ Handler expired",
                        description="Go back and try again",
                        input_message_content=InputTextMessageContent(
                            message_text="⚠️ <b>Handler expired!</b>",
                            parse_mode="HTML"
                        )
                    )
                ], cache_time=0, is_personal=True)
                return True

        # Parse: cfg <module> [key] - browse config
        parts = q.split(maxsplit=2)
        if len(parts) < 2:
            # Show all modules
            modules = get_modules()
            if not modules:
                await query.answer(results=[
                    InlineQueryResultArticle(
                        id="no_modules",
                        title="❌ No modules",
                        description="No configurable modules found",
                        input_message_content=InputTextMessageContent(
                            message_text="❌ <b>No configurable modules found</b>",
                            parse_mode="HTML"
                        )
                    )
                ], cache_time=60, is_personal=True)
                return True

            results = []
            for m in modules:
                results.append(InlineQueryResultArticle(
                    id=f"mod_{m['name']}",
                    title=f"📦 {m['name']}",
                    description=f"{len(m['keys'])} configurable keys",
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"🕊 <b>Configurator: {m['name']}</b>\n\n"
                            f"<i>Keys:</i>\n" +
                            "\n".join(
                                f"• <code>{k['name']}</code> ({k.get('type', 'str')})" for k in m['keys'])
                        ),
                        parse_mode="HTML"
                    )
                ))

            await query.answer(results=results, cache_time=60, is_personal=True)
            return True

        module_name = parts[1]
        modules = get_modules()
        mod = next((m for m in modules if m["name"] == module_name), None)

        if not mod:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="mod_not_found",
                    title="❌ Module not found",
                    description=f"Module '{module_name}' not found",
                    input_message_content=InputTextMessageContent(
                        message_text=f"❌ <b>Module '{module_name}' not found</b>",
                        parse_mode="HTML"
                    )
                )
            ], cache_time=60, is_personal=True)
            return True

        if len(parts) < 3:
            # Show module keys
            results = []
            for k in mod['keys']:
                cur_val = get(module_name, k['name'], k['default'])
                results.append(InlineQueryResultArticle(
                    id=f"key_{module_name}_{k['name']}",
                    title=f"🔧 {k['name']}",
                    description=f"Current: {cur_val} | Type: {k.get('type', 'str')}",
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"🕊 <b>{module_name}.{k['name']}</b>\n\n"
                            f"├─ <i>current</i>: <code>{cur_val}</code>\n"
                            f"├─ <i>default</i>: <code>{k['default']}</code>\n"
                            f"└─ <i>type</i>: <code>{k.get('type', 'str')}</code>"
                        ),
                        parse_mode="HTML"
                    )
                ))

            await query.answer(results=results, cache_time=60, is_personal=True)
            return True

        # Show specific key
        key_name = parts[2]
        key_info = next(
            (k for k in mod['keys'] if k['name'] == key_name), None)

        if not key_info:
            await query.answer(results=[
                InlineQueryResultArticle(
                    id="key_not_found",
                    title="❌ Key not found",
                    description=f"Key '{key_name}' not found in module '{module_name}'",
                    input_message_content=InputTextMessageContent(
                        message_text=f"❌ <b>Key '{key_name}' not found in module '{module_name}'</b>",
                        parse_mode="HTML"
                    )
                )
            ], cache_time=60, is_personal=True)
            return True

        cur_val = get(module_name, key_name, key_info['default'])
        await query.answer(results=[
            InlineQueryResultArticle(
                id=f"edit_{module_name}_{key_name}",
                title=f"✏️ {module_name}.{key_name}",
                description=f"Current: {cur_val}",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"🕊 <b>{module_name}.{key_name}</b>\n\n"
                        f"├─ <i>current</i>: <code>{cur_val}</code>\n"
                        f"├─ <i>default</i>: <code>{key_info['default']}</code>\n"
                        f"└─ <i>type</i>: <code>{key_info.get('type', 'str')}</code>"
                    ),
                    parse_mode="HTML"
                )
            )
        ], cache_time=60, is_personal=True)
        return True


# Register on module load
@loader.events.on_load
async def _on_load(client):
    await _register_inline_query(client)
