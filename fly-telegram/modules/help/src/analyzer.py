#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

# eto takoi govnokod...

import ast
from pathlib import Path


class ModuleAnalyzer:
    """extract commands from file"""

    def __init__(self, modules_path: Path) -> None:
        self.modules_path = modules_path

    def get_modules(self) -> list[str]:
        """get all available modules"""
        modules: list[str] = []

        if not self.modules_path.exists():
            return modules

        for item in self.modules_path.iterdir():
            if (item.is_dir and
                not item.name.startswith("_") and
                    not item.name.startswith(".")):

                src_path = item / "src"
                if src_path.exists() and any(src_path.glob("*.py")):
                    modules.append(item.name)

        return sorted(modules)

    def cmd_info(self, file: Path) -> list[dict]:
        """extract info from command"""
        commands: list[dict] = []

        try:
            with open(file, encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.endswith("_cmd"):
                    name: str = node.name[:-4]  # _cmd

                    docstring: str = ast.get_docstring(node) or ""

                    args: list[str] = []
                    for arg in node.args.args:
                        arg_name: str = arg.arg
                        if arg_name != "self":
                            args.append(arg_name)

                    commands.append({
                        'name': name,
                        'docstring': docstring,
                        'arguments': args,
                        'file': file.name,
                        'module': file.parent.parent.name
                    })
        except Exception:
            pass

        return commands

    def module_commands(self, name: str) -> list[dict]:
        """get all commands from module"""
        commands: list[dict] = []
        module_dir: Path = self.modules_path / name / "src"

        if not module_dir.exists():
            return commands

        for file in module_dir.glob("*.py"):
            file_cmds: list[dict] = self.cmd_info(file)
            commands.extend(file_cmds)

        return commands
