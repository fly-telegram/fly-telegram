#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import json
import logging
import os
import sys
from typing import Optional, Tuple

from pyrogram import Client, errors, types
from pyrogram.enums import ParseMode

from .utils import SESSION_FILE
from .web import Web


class Auth:
    def __init__(self):
        self.config = self._load_config("config.json")
        self.client = Client(
            SESSION_FILE,
            parse_mode=ParseMode.HTML,
            **{k: self.config[k] for k in ("api_id", "api_hash")},
            device_model=self.config.get("device_model", " fly-telegram"),
        )

        self.web = Web(self.client)

    @staticmethod
    def _load_config(file_path: str) -> dict:
        with open(file_path) as f:
            return json.load(f)

    async def _get_input(self, prompt: str, error_msg: Optional[str] = None) -> str:
        while True:
            value = input(prompt).strip()
            if value:
                return value
            if error_msg:
                logging.error(error_msg)

    async def send_code(self) -> Tuple[str, str]:
        errors_to_catch = (
            errors.PhoneNumberInvalid,
            errors.PhoneNumberBanned,
            errors.PhoneNumberFlood,
            errors.PhoneNumberUnoccupied,
            errors.BadRequest,
        )

        while True:
            phone = await self._get_input("Phone number: ", "Phone number cannot be empty!")
            try:
                sent_code = await self.client.send_code(phone)
                return phone, sent_code.phone_code_hash
            except errors_to_catch as e:
                logging.error(f"Error: {e}. Please try again.")

    async def enter_code(self, phone: str, code_hash: str) -> Optional[types.User]:
        code = await self._get_input("Verification code: ", "Code cannot be empty!")
        try:
            return await self.client.sign_in(phone, code_hash, code)
        except errors.SessionPasswordNeeded:
            return None

    async def enter_2fa(self) -> types.User:
        while True:
            password = await self._get_input("2FA password: ", "Password cannot be empty!")
            try:
                return await self.client.check_password(password)
            except errors.BadRequest:
                logging.error("Invalid 2FA password. Try again")

    async def load(self, web=True) -> Tuple[Client, types.User]:
        await self.client.connect()

        try:
            me = await self.client.get_me()

        except errors.AuthKeyUnregistered:
            if web:
                await self.web.run()
            else:
                phone, code_hash = await self.send_code()
                me = await self.enter_code(phone, code_hash) or await self.enter_2fa()

        except errors.SessionRevoked:
            logging.error("Session revoked! Removing session file...")
            os.remove(SESSION_FILE)
            await self.client.disconnect()
            sys.exit(64)

        return self.client, me
