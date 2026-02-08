#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import getpass
import sys

from . import arguments, main

PYTHON_VERSION = (3, 9, 0)

args = arguments.parser()


def check():

    if getpass.getuser() == "root" and not args.root:
        print('Running the userbot with root access can be dangerous!')
        print('Run the userbot with the parameter "--root" if you want to skip this error!')
        sys.exit(1)

    if sys.version_info < PYTHON_VERSION and not args.old:
        print('Your Python version is old!')
        print(f'Use version {".".join(map(str, PYTHON_VERSION))}')
        print('If you want to skip this error, use the "--old" parameter to run on older versions. There may be errors!')
        sys.exit(1)

    if __package__ != "fly-telegram":
        print("You cannot run this as a script")
        sys.exit(1)


if __name__ == "__main__":
    check()
    level = args.log_level if hasattr(
        args, 'log_level') and args.log_level else "info"
    main.userbot.main(level, args.no_web)
