#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

from typing import List, Optional

class Manager:
    """modules varible manager"""
    def __init__(self) -> None:
        self.modules: dict = {}

    def add_module(self, name: str, commands: List[str]) -> dict:
        self.modules[name] = commands
        return self.modules
    
    def remove_module(self, name: str) -> dict:
        del self.modules[name]
        return self.modules
    
    def get_modules(self) -> dict:
        return self.modules

manager = Manager()