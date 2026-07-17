#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

"""The help command"""

from inline import InlineCall

from .analyzer import ModuleAnalyzer


async def help_cmd(self):
    """get all modules and commands"""
    analyzer = ModuleAnalyzer(self.client.loader.modules_path)

    modules = analyzer.get_modules()

    if not modules:
        await self.message.edit(self.lang.get("modules_not_found"))
        return

    items = []
    for module in modules:
        get_commands = analyzer.module_commands(module)
        if commands := [command.get("name") for command in get_commands]:
            items.append((module, commands))

        items.sort(key=lambda x: (len(x[1]), x[0]))

        all_commands = "\n".join(
            f"├─ 📦 <b>{module}</b>: [ <code>{', '.join(commands)}</code> ]"
            if i < len(items) - 1
            else f"└─ 📦 <b>{module}</b>: [ <code>{', '.join(commands)}</code> ]"
            for i, (module, commands) in enumerate(items)
        )

    await self.message.edit(f"{self.lang.get('all_commands')}\n{all_commands}")


async def support_cmd(self):
    await self.message.delete()
    inline = self.client.inline
    await inline.say(
        self.client,
        self.message,
        self.lang.get("support_question"),
        prefix="help_support_",
        buttons=[
            [
                {
                    "text": self.lang.get("yes"),
                    "callback": yes_handler,
                }
            ],
            [
                {
                    "text": self.lang.get("no"),
                    "callback": no_handler,
                }
            ],
        ],
    )


async def yes_handler(call: InlineCall):
    await call.client.join_chat("t.me/flyTG_support")
    await call.bot.edit_message_text(
        text=(call.lang.get("joined") + '<a href="https://t.me/flyTG_support">' + call.lang.get("support_chat") + "</a>"),
        parse_mode="HTML",
        inline_message_id=call.inline_message_id,
    )


async def no_handler(call: InlineCall):
    await call.bot.edit_message_text(
        text=call.lang.get("cancelled"), parse_mode="HTML", inline_message_id=call.inline_message_id
    )
