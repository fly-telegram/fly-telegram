#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import base64
import json
import logging
import os
import sys
from typing import Optional, Tuple

from pyrogram import Client, errors, types
from pyrogram.enums import ParseMode

from telethon.crypto import AuthKey
from telethon import TelegramClient
from telethon.sessions import MemorySession

from .web import Web
from .utils import SESSION_FILE

TELEGRAM_SERVERS = {
    "TEST": {
        1: "149.154.175.10",
        2: "149.154.167.40",
        3: "149.154.175.117",
    },
    "PROD": {
        1: "149.154.175.53",
        2: "149.154.167.51",
        3: "149.154.175.100",
        4: "149.154.167.91",
        5: "91.108.56.130",
        203: "91.105.192.100",
    }
}


class Auth:
    def __init__(self):
        self.config = self._load_config("config.json")
        self.client = Client(
            SESSION_FILE,
            parse_mode=ParseMode.HTML,
            **{k: self.config[k] for k in ("api_id", "api_hash")},
            device_model=self.config.get("device_model", " fly-telegram"),
        )
        self.tl_client = None

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

    async def convector(self) -> TelegramClient:
        session_string = await self.client.export_session_string()
        try:
            # Create a new MemorySession
            session = MemorySession()

            # Get DC information from Pyrogram session
            dc_id = self.client.session.dc_id
            ip = TELEGRAM_SERVERS["PROD"].get(dc_id)

            # Set DC information
            session.set_dc(
                dc_id=dc_id,
                server_address=ip,
                port=443
            )

            # Convert session string to AuthKey
            from telethon.crypto import AuthKey
            auth_key = AuthKey(data=base64.urlsafe_b64decode(
                session_string + '=' * (-len(session_string) % 4)))

            # Set the auth key for the session
            session.auth_key = auth_key

            return TelegramClient(
                session,
                self.config["api_id"],
                self.config["api_hash"]
            )

        except Exception as e:
            logging.error(f"Error converting session: {e}")
            raise ValueError("Failed to convert session") from e

    async def load(self, web=False, tl_session=False) -> Tuple[Client, types.User]:
        await self.client.connect()

        try:
            me = await self.client.get_me()

            if tl_session:
                logging.debug("Telethon converting...")
                self.tl_client = await self.convector()
                await self.tl_client.start()

                tl_me = await self.tl_client.get_me()
                logging.debug("Telethon client is started.")

                if me.id != tl_me.id:
                    raise RuntimeError(
                        "The telethon session and pyrogram were not converted.")

        except errors.AuthKeyUnregistered:
            if web:
                await self.web.run()
            else:
                phone, code_hash = await self.send_code()
                me = await self.enter_code(phone, code_hash) or await self.enter_2fa()

            self.tl_client = await self.convector()
            await self.tl_client.start()
        except errors.SessionRevoked:
            logging.error("Session revoked! Removing session file...")
            os.remove(SESSION_FILE)
            await self.client.disconnect()
            sys.exit(64)

        return self.client, self.tl_client, me
