#         _______  _____   ___ ___  _______  _______
#        |    ___||     |_|   |   ||_     _||     __|
#        |    ___||       |\     /   |   |  |    |  |
#        |___|    |_______| |___|    |___|  |_______|
#                      t.me/FLYTG_UB
#
#            🔒 Licensed under the GNU-APGL 3.0
#             www.gnu.org/licenses/agpl-3.0.html

import ast
from inline import inline

def insert_returns(body):
    if isinstance(body[-1], ast.Expr):
        body[-1] = ast.Return(body[-1].value)
        ast.fix_missing_locations(body[-1])
        if isinstance(body[-1], ast.If):
            insert_returns(body[-1].body)
            insert_returns(body[-1].orelse)
        if isinstance(body[-1], ast.With):
            insert_returns(body[-1].body)

async def run_code(code, env={}):
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
    
async def eval_cmd(self, code):
    """The eval command for execute python code."""
    result = await run_code(
        code,
        {
            "self": self,
            "client": self.client,
            "app": self.client,
            "bot": inline.bot,
            "message": self.message,
            "pyrogram": __import__("pyrogram")
        }
    )

    if getattr(result, "stringify", ""):
        try:
            result = str(result.stringify())
        except:  # noqa: E722
            pass
    
    await message.edit(
        "<b>🐍 Python code:</b>\n"
        f"<pre language='python'>{code}</pre>\n"
        f"<b>📀 Result: </b>\n"
        f"<pre language='python'>{result}</pre>"
    )