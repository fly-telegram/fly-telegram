#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the CC-by-NC
#           creativecommons.org/licenses/by-nc/4.0/


import base64
import io
import os

import qrcode
import qrcode.image.svg
import uvicorn
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pyrogram import Client, errors
from pyrogram.raw.functions.auth import ExportLoginToken, ImportLoginToken
from pyrogram.raw.types.auth import LoginTokenSuccess, LoginTokenMigrateTo


class Web:
    def __init__(self, client: Client):
        """
        The webUI backend
        Args:
            client (pyrogram.Client): The pyrogram client object
        """
        self.app = FastAPI()
        self._setup_web()
        self.client = client
        self.server = None
        self.qr_token = None

    def _setup_web(self):
        """
        Setup the webUI
        """
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )

        currentdir = os.path.dirname(os.path.abspath(__file__))
        staticdir = os.path.join(currentdir, "static")
        templatesdir = os.path.join(currentdir, "templates")

        self.app.mount(
            "/static/", StaticFiles(directory=staticdir), name="static")
        self.templates = Jinja2Templates(directory=templatesdir)

        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            return self.templates.TemplateResponse(request=request, name="index.html", context={"request": request})

        @self.app.post("/send_code")
        async def send_code(phone: str = Form(...)):
            if not self.client.is_connected:
                await self.client.connect()

            try:
                sent_code = await self.client.send_code(phone)
                return JSONResponse(content={"code_hash": sent_code.phone_code_hash})
            except errors.PhoneNumberInvalid:
                raise HTTPException(
                    status_code=400, detail="Invalid phone number")
            except errors.PhoneNumberBanned:
                raise HTTPException(
                    status_code=400, detail="Phone number banned")
            except errors.PhoneNumberFlood:
                raise HTTPException(
                    status_code=400, detail="Phone number flood")
            except errors.PhoneNumberUnoccupied:
                raise HTTPException(
                    status_code=400, detail="Phone number unoccupied")
            except errors.BadRequest:
                raise HTTPException(status_code=400, detail="Bad request")

        @self.app.post("/sign_in")
        async def sign_in(phone: str = Form(...), code_hash: str = Form(...), code: str = Form(...), password: str = Form(None)):
            if not self.client.is_connected:
                await self.client.connect()

            try:
                if password:
                    user = await self.client.check_password(password)
                else:
                    user = await self.client.sign_in(phone, code_hash, code)

                response = JSONResponse(
                    content={"user": user.first_name, "status": "success"})

                await self.client.storage.user_id(user.id)
                await self.client.storage.is_bot(False)

                if self.server:
                    self.server.should_exit = True
                    # await self.server.shutdown()

                return response
            except errors.SessionPasswordNeeded:
                return JSONResponse(content={"status": "2fa_required"}, status_code=401)
            except errors.BadRequest:
                raise HTTPException(status_code=402, detail="Invalid code")
            except Exception as err:
                raise HTTPException(status_code=403, detail=str(err))

        @self.app.post("/qr_init")
        async def qr_init():
            if not self.client.is_connected:
                await self.client.connect()

            try:
                result = await self.client.invoke(ExportLoginToken(
                    api_id=self.client.api_id,
                    api_hash=self.client.api_hash,
                    except_ids=[]
                ))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

            if isinstance(result, LoginTokenSuccess):
                me = await self.client.get_me()
                return {"status": "already_logged_in", "user": me.first_name}

            self.qr_token = result.token
            token_b64 = base64.urlsafe_b64encode(
                result.token).rstrip(b'=').decode()
            url = f"tg://login?token={token_b64}"

            qr = qrcode.QRCode()
            qr.add_data(url)
            qr.make()
            img = qr.make_image(
                image_factory=qrcode.image.svg.SvgPathFillImage)
            svg_buf = io.BytesIO()
            img.save(svg_buf)
            svg_str = svg_buf.getvalue().decode()

            return {
                "token_b64": token_b64,
                "qr_svg": svg_str,
                "status": "waiting"
            }

        @self.app.post("/qr_poll")
        async def qr_poll():
            if not self.client.is_connected:
                await self.client.connect()

            if not self.qr_token:
                raise HTTPException(status_code=400, detail="No QR session")

            try:
                result = await self.client.invoke(ImportLoginToken(token=self.qr_token))
            except Exception:
                return JSONResponse(content={"status": "waiting"})

            if isinstance(result, LoginTokenSuccess):
                if self.server:
                    self.server.should_exit = True
                me = await self.client.get_me()
                await self.client.storage.user_id(me.id)
                await self.client.storage.is_bot(False)
                return {"status": "success", "user": me.first_name}

            if isinstance(result, LoginTokenMigrateTo):
                await self.client.disconnect()
                self.client.dc_id = result.dc_id
                await self.client.connect()
                self.qr_token = result.token
                try:
                    result2 = await self.client.invoke(ImportLoginToken(token=self.qr_token))
                except Exception:
                    return {"status": "waiting"}
                if isinstance(result2, LoginTokenSuccess):
                    if self.server:
                        self.server.should_exit = True
                    me = await self.client.get_me()
                    await self.client.storage.user_id(me.id)
                    await self.client.storage.is_bot(False)
                    return {"status": "success", "user": me.first_name}
                return {"status": "waiting"}

            return {"status": "waiting"}

    async def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Run the webUI

        Args:
            host (str): Client host
            port (int): Client port

        Returns:
            turple: The pyrogram.Client and get_me
        """
        config = uvicorn.Config(self.app, host=host, port=port)
        self.server = uvicorn.Server(config)
        await self.server.serve()

        me = await self.client.get_me()

        return self.client, me
