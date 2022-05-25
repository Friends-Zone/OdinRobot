# Module to blacklist users and prevent them from using commands by @TheRealPhoenix

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html
import tg_bot.modules.sql.blacklistusers_sql as sql
from .. import (
    DEV_USERS,
    MOD_USERS,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    SYS_ADMIN,
    WHITELIST_USERS,
    dispatcher,
)
from .helper_funcs.chat_status import dev_plus
from .helper_funcs.extraction import extract_user, extract_user_and_text
from .log_channel import gloggable
from .helper_funcs.decorators import kigcmd

BLACKLISTWHITELIST = (
    [OWNER_ID] + [SYS_ADMIN] + DEV_USERS + SUDO_USERS + WHITELIST_USERS + SUPPORT_USERS + MOD_USERS
)
BLABLEUSERS = [OWNER_ID] + DEV_USERS + [SYS_ADMIN]

@kigcmd(command='ignore', pass_args=True)
@dev_plus
@gloggable
def bl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("I doubt that's a user.")
        return ""

    if user_id == bot.id:
        message.reply_text("How am I supposed to do my work if I am ignoring myself?")
        return ""

    if user_id in BLACKLISTWHITELIST:
        message.reply_text("No!\nNoticing Super Users is my job.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message != 'User not found':
            raise
        message.reply_text("I can't seem to find this user.")
        return ''
    sql.blacklist_user(user_id, reason)
    message.reply_text("I shall ignore the existence of this user!")
    log_message = (
        f"#BLACKLIST\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(target_user.id, target_user.first_name)}"
    )
    if reason:
        log_message += f"\n<b>Reason:</b> {reason}"

    return log_message

@kigcmd(command='notice', pass_args=True)
@dev_plus
@gloggable
def unbl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text("I doubt that's a user.")
        return ""

    if user_id == bot.id:
        message.reply_text("I always notice myself.")
        return ""

    try:
        target_user = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user.")
            return ""
        else:
            raise

    if sql.is_user_blacklisted(user_id):

        sql.unblacklist_user(user_id)
        message.reply_text("*notices user*")
        log_message = (
            f"#UNBLACKLIST\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(target_user.id, target_user.first_name)}"
        )

        return log_message

    else:
        message.reply_text("I am not ignoring them at all though!")
        return ""

@kigcmd(command='ignoredlist', pass_args=True)
@dev_plus
def bl_users(update: Update, context: CallbackContext):
    users = []
    bot = context.bot
    for each_user in sql.BLACKLIST_USERS:
        user = bot.get_chat(each_user)
        if reason := sql.get_reason(each_user):
            users.append(f"• {mention_html(user.id, user.first_name)} :- {reason}")
        else:
            users.append(f"• {mention_html(user.id, user.first_name)}")

    message = "<b>Blacklisted Users</b>\n" + (
        "\n".join(users) if users else "Noone is being ignored as of yet."
    )

    update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)


def __user_info__(user_id):

    if user_id in (777000, 1087968824):
        return ""

    is_blacklisted = sql.is_user_blacklisted(user_id)


    if (
        user_id
        in [777000, 1087968824, dispatcher.bot.id]
        + SUDO_USERS
        + WHITELIST_USERS
        + SUPPORT_USERS
        + MOD_USERS
    ):
        return ""
    if is_blacklisted:
        text = "\nㅤBlacklisted: <b>{}</b>"
        text = text.format("Yes")
        if reason := sql.get_reason(user_id):
            text += f"\nㅤReason: <code>{reason}</code>"
    else:
        text = ""

    return text

__mod_name__ = "Blacklisting Users"
