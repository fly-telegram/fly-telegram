#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import argparse


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--no-logo",
        action="store_true",
        help="Disables the logo in the console.",
    )
    parser.add_argument(
        "--old",
        action="store_true",
        help="Ignore python version check",
    )
    parser.add_argument(
        "--root",
        action="store_true",
        help="Ignore root error",
    )

    return parser.parse_args()
