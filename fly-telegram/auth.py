#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

import asyncio
import base64
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import qrcode
from pyrogram import Client, errors, types
from pyrogram.enums import ParseMode
from pyrogram.raw.functions.auth import ExportLoginToken, ImportLoginToken
from pyrogram.raw.types.auth import LoginTokenMigrateTo, LoginTokenSuccess

from .storage import CustomStorage
from .utils import SESSION_FILE
from .web import Web


def _input_passwd() -> Optional[str]:
    """Input session password"""
    password = input("Input '.session' password encrypt (empty for none): ").strip()
    return password if password else None


class Auth:
    def __init__(self):
        self.config = self._load_config("config.json")

        session_file = Path(SESSION_FILE + ".session")
        session_password = self.config.get("passwd", None)
        if session_password is None and not session_file.exists():
            session_password = _input_passwd()
            if session_password:
                self.config["passwd"] = session_password
                self._save_config("config.json", self.config)
            else:
                logging.warning("Session encryption disabled (no password)")

        if session_password:
            workdir = Path(SESSION_FILE).parent
            session_name = Path(SESSION_FILE).stem
            storage = CustomStorage(
                name=session_name,
                workdir=workdir,
                password=session_password,
            )
        else:
            storage = None

        self.client = Client(
            SESSION_FILE,
            parse_mode=ParseMode.HTML,
            **{k: self.config[k] for k in ("api_id", "api_hash")},
            device_model=self.config.get("device_model", "fly-telegram"),
            proxy=self.config.get("proxy", None),
            storage_engine=storage,
        )

        self.web = Web(self.client)

    @staticmethod
    def _save_config(path: str, config: dict):
        """
        Save config to file
        Args:
            path (str): The file path
            config (dict): The data
        """
        with open(path, "w") as f:
            json.dump(config, f, indent=4)

    @staticmethod
    def _load_config(path: str) -> dict:
        """
        Load the config file

        Args:
            path (str): The file path

        Returns:
            dict: The config
        """
        if not os.path.exists(path):
            default = {
                "api_id": 12255822,
                "api_hash": "f626bf229077cae7b9e790606d4efb81",
                "device_model": "fly telegram",
                "test_mode": False,  # test DC telegram
                "proxy": {},  # pyrogram proxy
                "passwd": None,  # encrypt password for session file
            }
            with open(path, "w") as f:
                json.dump(default, f, indent=4)

            return default

        with open(path) as f:
            return json.load(f)

    async def _get_input(self, prompt: str, error_msg: Optional[str] = None) -> str:
        """
        Get input from user

        Args:
            prompt (str): the prompt
            error_msg (str): Error message
        Returns:
            str: The message
        """
        while True:
            if value := input(prompt).strip():
                return value
            if error_msg:
                logging.error(error_msg)

    async def send_code(self) -> tuple[str, str]:
        """
        Send code
        Retruns:
            tuple: The phone number and code hash
        """
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
        """
        Validate the code

        Args:
            phone (str): The phone number
            code_hash (str): The code hash
        Returns:
            pyrogram.types.User: the object
        """
        code = await self._get_input("Verification code: ", "Code cannot be empty!")
        try:
            return await self.client.sign_in(phone, code_hash, code)
        except errors.SessionPasswordNeeded:
            return None

    async def enter_2fa(self) -> types.User:
        """
        Validate 2FA password
        Retruns:
            pyrogram.types.User: the object
        """
        while True:
            password = await self._get_input("2FA password: ", "Password cannot be empty!")
            try:
                return await self.client.check_password(password)
            except errors.BadRequest:
                logging.error("Invalid 2FA password. Try again")

    async def login_qr(self) -> tuple[Client, types.User]:
        """
        Login via QR code
        Returns:
            tuple: The client and get_me
        """
        result = await self.client.invoke(
            ExportLoginToken(api_id=self.config["api_id"], api_hash=self.config["api_hash"], except_ids=[])
        )

        if isinstance(result, LoginTokenSuccess):
            me = await self.client.get_me()
            return self.client, me

        token_bytes = result.token
        token_b64 = base64.urlsafe_b64encode(token_bytes).rstrip(b"=").decode()
        url = f"tg://login?token={token_b64}"

        qr = qrcode.QRCode()
        qr.add_data(url)
        logging.info("Open your telegram app (Settings > Devices > Add new device) and scan")
        qr.print_ascii()

        while True:
            await asyncio.sleep(3)
            try:
                result = await self.client.invoke(ImportLoginToken(token=token_bytes))
            except Exception:
                continue

            if isinstance(result, LoginTokenSuccess):
                me = await self.client.get_me()
                await self.client.storage.user_id(me.id)
                await self.client.storage.is_bot(False)
                return self.client, me

            elif isinstance(result, LoginTokenMigrateTo):
                await self.client.disconnect()
                self.client.dc_id = result.dc_id
                await self.client.connect()
                try:
                    result2 = await self.client.invoke(ImportLoginToken(token=result.token))
                except Exception:
                    continue
                if isinstance(result2, LoginTokenSuccess):
                    me = await self.client.get_me()
                    await self.client.storage.user_id(me.id)
                    await self.client.storage.is_bot(False)
                    return self.client, me

    async def load(self, web=True, qr=False) -> tuple[Client, types.User]:
        """
        Load for auth user

        Args:
            web (bool): Login with webUI?
            qr (bool): Login via QR code?
        Returns:
            turple: The client and get_me
        """
        try:
            await self.client.connect()
            me = await self.client.get_me()
        except errors.AuthKeyUnregistered:
            if qr:
                return await self.login_qr()
            if web:
                self.client, me = await self.web.run()
            else:
                phone, code_hash = await self.send_code()
                me = await self.enter_code(phone, code_hash) or await self.enter_2fa()

        except errors.SessionRevoked:
            logging.error("Session revoked! Removing session file...")
            os.remove(SESSION_FILE + ".session")
            await self.client.disconnect()
            sys.exit(64)

        except KeyError:
            logging.error("Corrupted session detected! Removing session file...")
            session_path = SESSION_FILE + ".session"
            if os.path.exists(session_path):
                os.remove(session_path)
            await self.client.disconnect()
            sys.exit(64)

        return self.client, me
