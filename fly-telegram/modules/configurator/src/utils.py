import ast
import contextlib
from pathlib import Path

from database import database
from languages import getlang

MODULES_PATH = Path(__file__).parent.parent.parent


def get_type(node):
    if node is None:
        return "str"
    try:
        s = ast.unparse(node)
    except Exception:
        return "str"
    if "Choice" in s:
        return "choice"
    if "Boolean" in s:
        return "bool"
    if "Integer" in s:
        return "int"
    if "Float" in s:
        return "float"
    if "Link" in s:
        return "link"
    if "String" in s:
        return "str"
    return "str"


def get_keys(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    keys = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "ConfigValue" or isinstance(func, ast.Attribute) and func.attr == "ConfigValue":
            pass
        else:
            continue

        if not node.args:
            continue

        name_arg = node.args[0]
        if not isinstance(name_arg, ast.Constant) or not isinstance(name_arg.value, str):
            continue
        name = name_arg.value

        default = None
        if len(node.args) > 1:
            with contextlib.suppress(Exception):
                default = ast.literal_eval(node.args[1])

        validator_node = None
        for kw in node.keywords:
            if kw.arg == "validator":
                validator_node = kw.value
                break
        if validator_node is None and len(node.args) > 3:
            validator_node = node.args[3]

        vtype = get_type(validator_node)
        keys.append({"name": name, "default": default, "type": vtype})

    return keys


def get_modules():
    result = []
    for d in sorted(MODULES_PATH.iterdir()):
        if not d.is_dir() or d.name.startswith(("_", ".")):
            continue
        src = d / "src"
        if not src.exists():
            continue
        keys = []
        for f in src.glob("*.py"):
            try:
                source = f.read_text(encoding="utf-8")
            except Exception:
                continue
            keys.extend(get_keys(source))
        if keys:
            result.append({"name": d.name, "keys": keys})
    return result


def db(module):
    cfg = database.get("config", module)
    return cfg if isinstance(cfg, dict) else {}


def get(module, key, default=None):
    return db(module).get(key, default)


def set(module, key, value):
    cfg = db(module)
    cfg[key] = value
    all_cfg = database.get("config")
    if not isinstance(all_cfg, dict):
        all_cfg = {}
    all_cfg[module] = cfg
    database.set("config", all_cfg)


def fmt(value, vtype="str", lang=None):
    if lang is None:
        lang = getlang("configurator")
    if value is None or value == "":
        return lang.get("not_set") if "not_set" in lang else "<i>not set</i>"
    if vtype == "bool":
        return lang.get("on") if value else lang.get("off") if "off" in lang else "❌ off"
    return str(value)
