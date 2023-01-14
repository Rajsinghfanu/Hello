import html
import json
import re
from time import sleep

import requests
from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
    User,
)
from telegram.error import BadRequest, RetryAfter, Unauthorized
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html

import MissCutie.Database.chatbot_sql as sql
from MissCutie import dispatcher
from MissCutie.Handlers.validation import user_admin, user_admin_no_reply
from MissCutie.Handlers.filters import CustomFilters
from MissCutie.Plugins.Admin.log_channel import gloggable


@user_admin_no_reply
@gloggable
def chatbotrm(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    match = re.match(r"rm_chat\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        is_kuki = sql.rem_kuki(chat.id)
        if is_kuki:
            is_kuki = sql.rem_kuki(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"AI_DISABLED\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
        else:
            update.effective_message.edit_text(
                "Hey Darling 𝐌ɪꜱꜱ𝐂ᴜᴛɪᴇ Chatbot disable by {}.".format(
                    mention_html(user.id, user.first_name)
                ),
                parse_mode=ParseMode.HTML,
            )

    return ""


@user_admin_no_reply
@gloggable
def chatbotadd(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    match = re.match(r"add_chat\((.+?)\)", query.data)
    if match:
        user_id = match.group(1)
        chat: Optional[Chat] = update.effective_chat
        is_kuki = sql.set_kuki(chat.id)
        if is_kuki:
            is_kuki = sql.set_kuki(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"AI_ENABLE\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
        else:
            update.effective_message.edit_text(
                "Hey Darling 𝐌ɪꜱꜱ𝐂ᴜᴛɪᴇ Chatbot enable by {}.".format(
                    mention_html(user.id, user.first_name)
                ),
                parse_mode=ParseMode.HTML,
            )

    return ""


@user_admin
@gloggable
def kuki(update: Update, context: CallbackContext):
    update.effective_user
    message = update.effective_message
    msg = "Choose an option"
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text="Enable", callback_data="add_chat({})")],
            [InlineKeyboardButton(text="Disable", callback_data="rm_chat({})")],
        ]
    )
    message.reply_text(
        msg,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


def kuki_message(context: CallbackContext, message):
    reply_message = message.reply_to_message
    if message.text.lower() == "kuki":
        return True
    if reply_message:
        if reply_message.from_user.id == context.bot.get_me().id:
            return True
    else:
        return False


def chatbot(update: Update, context: CallbackContext):
    message = update.effective_message
    chat_id = update.effective_chat.id
    bot = context.bot
    is_kuki = sql.is_kuki(chat_id)
    if not is_kuki:
        return

    if message.text and not message.document:
        if not kuki_message(context, message):
            return
        Message = message.text
        bot.send_chat_action(chat_id, action="typing")
        kukiurl = requests.get(
            f"https://kukiapi.xyz/api/apikey=5281955434-KUKIyq4NCB2Ca8/himawari/@nekoarsh/message={Message}"
        )

        Kuki = json.loads(kukiurl.text)
        kuki = Kuki["reply"]
        sleep(0.3)
        message.reply_text(kuki, timeout=60)


def list_all_chats(update: Update, context: CallbackContext):
    chats = sql.get_all_kuki_chats()
    text = "<b>𝐌ɪꜱꜱ𝐂ᴜᴛɪᴇ Enabled Chats</b>\n"
    for chat in chats:
        try:
            x = context.bot.get_chat(int(*chat))
            name = x.title or x.first_name
            text += f"• <code>{name}</code>\n"
        except (BadRequest, Unauthorized):
            sql.rem_kuki(*chat)
        except RetryAfter as e:
            sleep(e.retry_after)
    update.effective_message.reply_text(text, parse_mode="HTML")


__help__ = """
*Admins only Commands*:
  • `/Chatbot`*:* Shows chatbot control panel
  
*Powered By* `https://chat.kuki.ai/`
"""

__mod_name__ = "ChatBot"


CHATBOTK_HANDLER = CommandHandler("chatbot", kuki, run_async=True)
ADD_CHAT_HANDLER = CallbackQueryHandler(chatbotadd, pattern=r"add_chat", run_async=True)
RM_CHAT_HANDLER = CallbackQueryHandler(chatbotrm, pattern=r"rm_chat", run_async=True)
CHATBOT_HANDLER = MessageHandler(
    Filters.text
    & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!") & ~Filters.regex(r"^\/")),
    chatbot,
    run_async=True,
)
LIST_ALL_CHATS_HANDLER = CommandHandler(
    "allchats", list_all_chats, filters=CustomFilters.dev_filter, run_async=True
)

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(CHATBOTK_HANDLER)
dispatcher.add_handler(RM_CHAT_HANDLER)
dispatcher.add_handler(LIST_ALL_CHATS_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)

__handlers__ = [
    ADD_CHAT_HANDLER,
    CHATBOTK_HANDLER,
    RM_CHAT_HANDLER,
    LIST_ALL_CHATS_HANDLER,
    CHATBOT_HANDLER,
]
