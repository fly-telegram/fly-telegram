#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
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
    parser.add_argument(
        "--log-level",
        type=str.lower,
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Run Fly-Telegram with log level"
    )
    parser.add_argument(
        "--token",
        help="Manyally set inline bot token"
    )

    return parser.parse_args()
