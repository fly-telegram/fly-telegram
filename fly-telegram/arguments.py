"""arguments parser (from friendly-telegram)"""
#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the CC-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import argparse


def parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-logo",
        action="store_true",
        help="Disables the logo in the console.",
    )
    parser.add_argument(
        "--root",
        action="store_true",
        help="Disable root check.",
    )
    parser.add_argument(
        "--old",
        action="store_true",
        help="Disable python version check.",
    )
    parser.add_argument(
        "--log-level",
        action="store",
        type=str,
        help="Logging level.",
        required=False,
    )
    parser.add_argument(
        "--no-web",
        action="store_false",
        help="Disable webUI for login. Using CLI interface"
    )

    return parser.parse_args()
