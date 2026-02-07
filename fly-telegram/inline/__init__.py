#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

from aiogram import Bot

from .call import InlineCall
from .keyboards import make_keyboard
from .main import Inline

inline = Inline()
inline.bot = Bot.get_current() # type: ignore

__all__ = ["InlineCall", "make_keyboard"]
