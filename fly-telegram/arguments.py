#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import argparse


def parser() -> argparse.Namespace:
    """
    parse arguments

    Returns:
        argparse.Namespace: The arguments
    """
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
        type=str.lower,
        help="Logging level.",
        required=False,
    )
    parser.add_argument("--no-web", action="store_false", help="Disable webUI for login. Using CLI interface.")
    parser.add_argument(
        "--token",
        action="store",
        type=str,
        help="Manyally set inline token.",
        required=False,
    )
    parser.add_argument(
        "--qr",
        action="store_true",
        help="Login via QR code.",
    )

    return parser.parse_args()
