from pathlib import Path
from typing import Optional

try:
    import ujson as json  # noqa: F401
except ModuleNotFoundError:
    import json as json  # noqa: F811

from database import database

DEFAULT_LANG = "en"
_modules_path = None


def set_modules_path(path: Path) -> None:
    global _modules_path
    _modules_path = path


class _Lang(dict):
    def __init__(self, strings: dict, lang: str):
        super().__init__(strings)
        self.lang = lang

    def __missing__(self, key: str) -> str:
        return key


def langpack(modules_path: Optional[Path], module_name: str) -> _Lang:
    lang_raw = database.get("lang")
    lang = str(lang_raw) if isinstance(lang_raw, str) else DEFAULT_LANG

    if modules_path and module_name:
        pack_path = modules_path / module_name / "langpack.json"
        if pack_path.exists():
            try:
                with open(pack_path, encoding="utf-8") as f:
                    packs = json.load(f)
                strings = packs.get(lang) or packs.get("en") or {}
                return _Lang(strings, lang)
            except Exception:
                pass

    return _Lang({}, lang)


def getlang(module_name: str) -> _Lang:
    return langpack(_modules_path, module_name)
