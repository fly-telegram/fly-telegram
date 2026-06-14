from uuid import uuid4

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)


def genresult(title: str, description: str, text: str) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=title.lower().replace(" ", "_"),
        title=title,
        description=description,
        input_message_content=InputTextMessageContent(
            message_text=text, parse_mode="HTML"
        ),
    )


def _kb(call, buttons):
    via = call.client.inline.viamanager
    rows = []
    for row in buttons:
        line = []
        for b in row:
            if "switch_inline_query_current_chat" in b:
                line.append(
                    InlineKeyboardButton(
                        text=b["text"],
                        switch_inline_query_current_chat=b[
                            "switch_inline_query_current_chat"
                        ],
                    )
                )
                continue
            if "switch_inline_query" in b:
                line.append(
                    InlineKeyboardButton(
                        text=b["text"], switch_inline_query=b["switch_inline_query"]
                    )
                )
                continue
            cb = b.get("callback")
            if callable(cb):
                uid = str(uuid4())
                via.handlers[uid] = {"callback": cb,
                                     "params": b.get("params", {})}
                line.append(InlineKeyboardButton(
                    text=b["text"], callback_data=uid))
            else:
                line.append(
                    InlineKeyboardButton(
                        text=b["text"], callback_data=b["callback"])
                )
        rows.append(line)
    return InlineKeyboardMarkup(inline_keyboard=rows)
