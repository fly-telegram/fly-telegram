#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#              🔒 Licensed under the СС-by-NC
#           creativecommons.org/licenses/by-nc/4.0/

# IDEA: github@BadPrivacyclub/rust-fly-telegram.git

import logging
from pathlib import Path
from typing import Optional

from pyrogram.storage.sqlite_storage import SQLiteStorage
from pyrogram.storage.sqlite_storage import TEST, PROD

log = logging.getLogger(__name__)


class CustomStorage(SQLiteStorage):
    def __init__(
        self,
        name: str,
        workdir: Path,
        password: str,
        session_string: Optional[str] = None,
        in_memory: bool = False,
        use_wal: bool = False,
    ):
        super().__init__(
            name=name,
            workdir=workdir,
            session_string=session_string,
            in_memory=in_memory,
            use_wal=use_wal,
        )
        self._passwd = password

    async def open(self):
        """open encrypted database"""
        if self.in_memory:
            from sqlcipher3 import dbapi2 as sqlite3

            self.conn = sqlite3.connect(
                ":memory:", timeout=1, check_same_thread=False)
            self.conn.set_key(self._passwd)
            await self.create()

            if self.session_string:
                await self._session_string()
            return

        path = self.database
        exists = isinstance(path, Path) and path.is_file()

        from sqlcipher3 import dbapi2 as sqlite3

        self.conn = sqlite3.connect(
            str(path), timeout=1, check_same_thread=False)
        self.conn.set_key(self._passwd)

        if self.use_wal:
            self.conn.execute("PRAGMA journal_mode=WAL")
        else:
            self.conn.execute("PRAGMA journal_mode=DELETE")

        if exists:
            await self.update()
        else:
            await self.create()

        with self.conn:
            self.conn.execute("VACUUM")

    async def close(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            self.conn = None

    async def _session_string(self):
        """in memory import database"""
        import base64
        import struct

        if len(self.session_string) in [
            self.SESSION_STRING_SIZE,
            self.SESSION_STRING_SIZE_64,
        ]:
            dc_id, test_mode, auth_key, user_id, is_bot = struct.unpack(
                (
                    self.OLD_SESSION_STRING_FORMAT
                    if len(self.session_string) == self.SESSION_STRING_SIZE
                    else self.OLD_SESSION_STRING_FORMAT_64
                ),
                base64.urlsafe_b64decode(
                    self.session_string + "=" * (-len(self.session_string) % 4)
                ),
            )

            await self.dc_id(dc_id)
            await self.test_mode(test_mode)
            await self.auth_key(auth_key)
            await self.user_id(user_id)
            await self.is_bot(is_bot)
            await self.date(0)

            log.warning("Old session string. Please re-login")
            return

        dc_id, api_id, test_mode, auth_key, user_id, is_bot = struct.unpack(
            self.SESSION_STRING_FORMAT,
            base64.urlsafe_b64decode(
                self.session_string + "=" * (-len(self.session_string) % 4)
            ),
        )

        await self.dc_id(dc_id)

        if test_mode:
            await self.server_address(TEST[dc_id])
            await self.port(80)
        else:
            await self.server_address(PROD[dc_id])
            await self.port(443)

        await self.api_id(api_id)
        await self.test_mode(test_mode)
        await self.auth_key(auth_key)
        await self.user_id(user_id)
        await self.is_bot(is_bot)
        await self.date(0)
