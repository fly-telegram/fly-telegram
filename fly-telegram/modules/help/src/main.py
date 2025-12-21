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
        await self.message.edit("<b>modules not found</b>")
        return
    
    text = "📚 <b>All modules:<b>\n"

    for module in modules:
        get_commands = analyzer.module_commands(module)
        commands = []

        for command in get_commands:
            commands.append(command.name)
        
        formatted = ", ".join(commands)

        text += f"* <b>{module}<b>: ({formatted})\n"

    await self.message.edit(text)