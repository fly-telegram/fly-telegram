#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

from database import database
from inline import InlineCall
from languages import getlang
from loader import Loader, events

loader = Loader()

LANGUAGES = {
    "ru": "btn_ru",
    "en": "btn_en",
    "fr": "btn_fr",
    "ge": "btn_ge",
    "ua": "btn_ua",
    "kz": "btn_kz",
}


def buttons(lang):
    buttons = []
    for code, btn_key in LANGUAGES.items():
        buttons.append(
            {
                "text": lang.get(btn_key),
                "callback": setlang,
                "params": {"lang_code": code},
            }
        )
    return [buttons[:3], buttons[3:]]


async def _select(client):
    lang = getlang("language")
    await client.inline.say(
        client=client,
        message=None,
        text=lang.get("title"),
        buttons=buttons(lang),
        chat_id=client.me.id,
        prefix="language_",
    )


async def setlang(call: InlineCall, lang_code: str):
    database.set("lang", lang_code)
    lang = getlang("language")
    await call.edit_message(lang.get("done"))


@events.on_load
async def on_load(client):
    if not database.get("lang"):
        await _select(client)


async def language_cmd(self):
    await self.message.delete()
    lang = getlang("language")
    await self.client.inline.say(
        client=self.client,
        message=self.message,
        text=lang.get("title"),
        buttons=buttons(lang),
        prefix="language_",
    )
