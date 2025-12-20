#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

from typing import List

modules: dict = {}

def add_module(name: str, commands: List[str]) -> dict:
    modules[name] = commands
    return modules

def remove_module(name: str) -> dict:
    del modules[name]
    return modules