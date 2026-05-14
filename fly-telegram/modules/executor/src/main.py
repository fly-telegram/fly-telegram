#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLY_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

import ast

from database import database
from inline import InlineCall
from loader import Loader

from .utils import AsyncTerminal

loader = Loader()


def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])
        if isinstance(body[-1], ast.If):
            insert_returns(body[-1].body)
            insert_returns(body[-1].orelse)
        if isinstance(body[-1], ast.With):
            insert_returns(body[-1].body)


async def run_code(code, env=None):
    if env is None:
        env = {}
    try:
        fn_name = "_eval_expr"
        cmd = "\n".join(f" {i}" for i in code.splitlines())
        body = f"async def {fn_name}():\n{cmd}"
        parsed = ast.parse(body)
        body = parsed.body[0].body
        insert_returns(body)
        env = {"__import__": __import__, **env}
        exec(compile(parsed, filename="<ast>", mode="exec"), env)
        return await eval(f"{fn_name}()", env)
    except Exception as error:
        return error


@loader.alias('e')
async def eval_cmd(self, code):
    """The eval command for execute python code."""
    warning = database.get("executor", "warning")
    if not warning:
        await self.message.delete()
        inline = self.client.inline
        await inline.say(
            self.client,
            self.message,
            (
                '⚠️ <b>The command can be execute code directly '
                'through the userbot and has full access to your '
                'data. Be careful with it. \n'
                'Click the button "agree" to proceed.</b>'
            ),
            buttons=[
                [{
                    "text": "✅ Agree",
                    "callback": agree_handler,
                }],
            ]
        )
        return

    inline = self.client.inline
    result = await run_code(
        code,
        {
            "self": self,
            "client": self.client,
            "app": self.client,
            "bot": inline.bot,
            "db": database,
            "database": database,
            "message": self.message,
            "reply": self.message.reply_to_message,
            "pyrogram": __import__("pyrogram"),
            "sys": __import__("sys")
        }
    )

    if getattr(result, "stringify", ""):
        try:
            result = str(result.stringify())
        except Exception:
            pass

    await self.message.edit(
        "<b>🐍 Python code:</b>\n"
        f"<pre language='python'>{code}</pre>\n"
        f"<b>📀 Result: </b>\n"
        f"<pre language='python'>{result}</pre>"
    )


@loader.alias('term')
async def terminal_cmd(self, command: str):
    text = (
        "📼 <b>Command</b>: \n"
        f"<code>{command}</code>\n"
        "✨ <b>Result</b>: \n"
    )

    term = AsyncTerminal(self.message, command, text, 0.25)
    await term.run()


async def agree_handler(call: InlineCall):
    data = {
        "warning": True
    }
    database.set("executor", data)

    await call.bot.edit_message_text(
        text=(
            '✅ <b>This is message will no longer appear.\n'
            'For security reasons, please enter the command again.</b>'
        ),
        parse_mode="HTML",
        inline_message_id=call.inline_message_id
    )
