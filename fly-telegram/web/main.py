#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#              🔒 Licensed under the CC-by-NC
#           creativecommons.org/licenses/by-nc/4.0/


import os

import uvicorn
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pyrogram import Client, errors


class Web:
    def __init__(self, client: Client):
        self.app = FastAPI()
        self._setup_web()
        self.client = client
        self.server = None

    def _setup_web(self):
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

    async def run(self, host: str = "0.0.0.0", port: int = 8000):
        config = uvicorn.Config(self.app, host=host, port=port)
        self.server = uvicorn.Server(config)
        await self.server.serve()

        me = await self.client.get_me()

        return self.client, me
