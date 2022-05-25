import html

from .. import ALLOW_EXCL, CustomCommandHandler, dispatcher, spamcheck
from .disable import DisableAbleCommandHandler
from .helper_funcs.chat_status import (

    connection_status,
    dev_plus,

)
from .sql import cleaner_sql as sql
from telegram import ParseMode, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,

)
from .helper_funcs.decorators import kigcmd, kigmsg

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
)

CMD_STARTERS = ("/", "!") if ALLOW_EXCL else "/"
BLUE_TEXT_CLEAN_GROUP = 13
CommandHandlerList = (CommandHandler, CustomCommandHandler, DisableAbleCommandHandler)
command_list = [
    "cleanblue",
    "ignoreblue",
    "unignoreblue",
    "listblue",
    "ungignoreblue",
    "gignoreblue" "start",
    "help",
    "settings",
    "donate",
    "stalk",
    "aka",
    "leaderboard",
]

for handler_list in dispatcher.handlers:
    for handler in dispatcher.handlers[handler_list]:
        if any(isinstance(handler, cmd_handler) for cmd_handler in CommandHandlerList):
            command_list += handler.command

@kigmsg((Filters.command & Filters.chat_type.groups), group=BLUE_TEXT_CLEAN_GROUP)
def clean_blue_text_must_click(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    if chat.get_member(bot.id).can_delete_messages and sql.is_enabled(chat.id):
        fst_word = message.text.strip().split(None, 1)[0]

        if len(fst_word) > 1 and any(
            fst_word.startswith(start) for start in CMD_STARTERS
        ):

            command = fst_word[1:].split("@")
            chat = update.effective_chat

            if ignored := sql.is_command_ignored(chat.id, command[0]):
                return

            if command[0] not in command_list:
                message.delete()

@kigcmd(command='cleanbluetext', pass_args=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def set_blue_text_must_click(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    bot, args = context.bot, context.args
    user = update.effective_user
    if len(args) >= 1:
        val = args[0].lower()
        if val in ("off", "no"):
            sql.set_cleanbt(chat.id, False)
            reply = f"Bluetext cleaning has been disabled for <b>{html.escape(chat.title)}</b>"

            message.reply_text(reply, parse_mode=ParseMode.HTML)

        elif val in ("yes", "on"):
            sql.set_cleanbt(chat.id, True)
            reply = f"Bluetext cleaning has been enabled for <b>{html.escape(chat.title)}</b>"

            message.reply_text(reply, parse_mode=ParseMode.HTML)

        else:
            reply = "Invalid argument.Accepted values are 'yes', 'on', 'no', 'off'"
            message.reply_text(reply)
    else:
        clean_status = sql.is_enabled(chat.id)
        clean_status = "Enabled" if clean_status else "Disabled"
        reply = f"Bluetext cleaning for <b>{chat.title}</b> : <b>{clean_status}</b>"
        message.reply_text(reply, parse_mode=ParseMode.HTML)

@kigcmd(command='ignorecleanbluetext', pass_args=True)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def add_bluetext_ignore(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        if added := sql.chat_ignore_command(chat.id, val):
            reply = f"<b>{args[0]}</b> has been added to bluetext cleaner ignore list."
        else:
            reply = "Command is already ignored."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be ignored."
        message.reply_text(reply)

@kigcmd(command='unignorecleanbluetext', pass_args=True)
@spamcheck
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def remove_bluetext_ignore(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args

    if len(args) >= 1:
        val = args[0].lower()
        if removed := sql.chat_unignore_command(chat.id, val):
            reply = f"<b>{args[0]}</b> has been removed from bluetext cleaner ignore list."
        else:
            reply = "Command isn't ignored currently."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be unignored."
        message.reply_text(reply)

@kigcmd(command='ignoreglobalcleanbluetext', pass_args=True)
@dev_plus
def add_bluetext_ignore_global(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        if added := sql.global_ignore_command(val):
            reply = f"<b>{args[0]}</b> has been added to global bluetext cleaner ignore list."

        else:
            reply = "Command is already ignored."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be ignored."
        message.reply_text(reply)

@kigcmd(command='unignoreglobalcleanbluetext', pass_args=True)
@dev_plus
def remove_bluetext_ignore_global(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        if removed := sql.global_unignore_command(val):
            reply = f"<b>{args[0]}</b> has been removed from global bluetext cleaner ignore list."

        else:
            reply = "Command isn't ignored currently."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be unignored."
        message.reply_text(reply)

@kigcmd(command='listcleanbluetext')
@dev_plus
def bluetext_ignore_list(update: Update, context: CallbackContext):

    message = update.effective_message
    chat = update.effective_chat

    global_ignored_list, local_ignore_list = sql.get_all_ignored(chat.id)
    text = ""

    if global_ignored_list:
        text = "The following commands are currently ignored globally from bluetext cleaning :\n"

        for x in global_ignored_list:
            text += f" - <code>{x}</code>\n"

    if local_ignore_list:
        text += "\nThe following commands are currently ignored locally from bluetext cleaning :\n"

        for x in local_ignore_list:
            text += f" - <code>{x}</code>\n"

    if text == "":
        text = "No commands are currently ignored from bluetext cleaning."
        message.reply_text(text)
        return

    message.reply_text(text, parse_mode=ParseMode.HTML)
    return

from .language import gs

def get_help(chat):
    return gs(chat, "cleaner_help")

__mod_name__ = "Cleaner"
