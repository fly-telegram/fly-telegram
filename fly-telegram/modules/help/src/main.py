#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

"""The help command"""
from .analyzer import ModuleAnalyzer

async def help_cmd(self):
    """get all modules and commands"""
    analyzer = ModuleAnalyzer(self.client.loader.modules_path)

    modules = analyzer.get_modules()

    if not modules:
        await self.message.edit("❌ <b>modules not found</b>")
        return
    
    items = []
    for module in modules:
        get_commands = analyzer.module_commands(module)
        commands = [command.get('name') for command in get_commands]
        if commands:
            items.append((module, commands))
        
        items.sort(key=lambda x: (len(x[1]), x[0]))

        all_commands = "\n".join(
        f"├─ 📦 <b>{module}</b>: [ <code>{', '.join(commands)}</code> ]" if i < len(items) - 1 else
        f"└─ 📦 <b>{module}</b>: [ <code>{', '.join(commands)}</code> ]"
        for i, (module, commands) in enumerate(items)
    )
    
    await self.message.edit(f"🕊 <b>All commands</b>\n{all_commands}")

async def support_cmd(self):
    await self.client.join_chat("t.me/flyTG_support")
    await self.message.edit(
        '🕊 <b>Joined to</b> ' + 
        '<a href="https://t.me/flyTG_support">support chat</a>'
    )