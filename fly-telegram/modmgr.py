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
    _inst = None
    _modules = {}

    def __new__(cls) -> None:
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst
    
    @classmethod
    def get_instance(cls):
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    def add_module(self, name: str, commands: List[str]) -> dict:
        self._modules[name] = commands
        return self._modules
    
    def remove_module(self, name: str) -> dict:
        del self._modules[name]
        return self._modules
    
    def get_modules(self) -> dict:
        return self._modules.copy()

manager = Manager.get_instance()