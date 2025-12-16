#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

from typing import List, Optional

modules: dict = {}

class Manager:
    """modules varible manager"""
    
    def add_module(self, name: str, commands: List[str]) -> dict:
        modules[name] = commands
        return modules
    
    def remove_module(self, name: str) -> dict:
        del modules[name]
        return modules
    
    def get_modules(self) -> dict:
        return modules

manager = Manager()