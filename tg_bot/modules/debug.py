import datetime
import os

from telegram import Update
from telegram.ext import CallbackContext

from .. import API_HASH, APP_ID, BACKUP_PASS, CASH_API_KEY, CF_API_KEY, DB_URI, LASTFM_API_KEY, TIME_API_KEY, TOKEN, dispatcher, spamwatch_api
from .helper_funcs.chat_status import dev_plus
from .helper_funcs.decorators import kigcmd, register

DEBUG_MODE = False

@kigcmd(command='debug')
@dev_plus
def debug(update: Update, _: CallbackContext):
    global DEBUG_MODE
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    print(DEBUG_MODE)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            DEBUG_MODE = True
            message.reply_text("Debug mode is now on.")
        elif args[1] in ("no", "off"):
            DEBUG_MODE = False
            message.reply_text("Debug mode is now off.")
    elif DEBUG_MODE:
        message.reply_text("Debug mode is currently on.")
    else:
        message.reply_text("Debug mode is currently off.")

@kigcmd(command='spamdebug')
@dev_plus
def asdebug(update: Update, context: CallbackContext):
    global IS_DEBUG
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    print(IS_DEBUG)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            IS_DEBUG = True
            message.reply_text("Antispam Debug mode is now on.")
        elif args[1] in ("no", "off"):
            IS_DEBUG = False
            message.reply_text("Antispam Debug mode is now off.")
    elif IS_DEBUG:
        message.reply_text("Antispam Debug mode is currently on.")
    else:
        message.reply_text("Antispam Debug mode is currently off.")

@kigcmd(command='gannounce')
@dev_plus
def asdebug(update: Update, context: CallbackContext):
    global GLOBALANNOUNCE
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    print(GLOBALANNOUNCE)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            GLOBALANNOUNCE = True
            message.reply_text("Global announcement is now on.")
        elif args[1] in ("no", "off"):
            GLOBALANNOUNCE = False
            message.reply_text("Global announcement is now off.")
    elif GLOBALANNOUNCE:
        message.reply_text("Global announcement is currently on.")
    else:
        message.reply_text("Global announcement is currently off.")

@kigcmd(command='spamcheck')
@dev_plus
def astoggle(update: Update, context: CallbackContext):
    global ANTISPAM_TOGGLE
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message
    print(ANTISPAM_TOGGLE)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            ANTISPAM_TOGGLE = True
            message.reply_text("Antispam module is now on.")
        elif args[1] in ("no", "off"):
            ANTISPAM_TOGGLE = False
            message.reply_text("Antispam module is now off.")
    elif ANTISPAM_TOGGLE:
        message.reply_text("Antispam module is currently on.")
    else:
        message.reply_text("Antispam module is currently off.")

@register(pattern='.*')
async def i_do_nothing_yes(event):
    global DEBUG_MODE
    if DEBUG_MODE:
        print(f"-{event.from_id} ({event.chat_id}) : {event.text}")
        if os.path.exists("updates.txt"):
            with open("updates.txt", "r") as f:
                text = f.read()
            with open("updates.txt", "w+") as f:
                f.write(f"{text}\n-{event.from_id} ({event.chat_id}) : {event.text}")
        else:
            with open("updates.txt", "w+") as f:
                f.write(
                    f"- {event.from_id} ({event.chat_id}) : {event.text} | {datetime.datetime.now()}"
                )


@kigcmd(command='logs')
@dev_plus
def logs(update: Update, context: CallbackContext):

    if not os.path.exists('logs.txt'):
        update.effective_message.reply_text("File doesn't exist")
        return

    user = update.effective_user

    logsname = f"{dispatcher.bot.username}_logs.txt"

    # https://pythonexamples.org/python-replace-string-in-file/
    logstxt = open("logs.txt", "rt")
    with open(logsname, "wt") as logsout:
        for line in logstxt:
            logsout.write(line.replace(str(DB_URI), '$DATABASE').replace(str(TOKEN), '$TOKEN').replace(str(APP_ID), '$APP_ID').replace(str(API_HASH), '$API_HASH').replace(str(CASH_API_KEY), '$CASH_API_KEY').replace(str(TIME_API_KEY), '$TIME_API_KEY').replace(str(LASTFM_API_KEY), '$LASTFM_API_KEY').replace(str(CF_API_KEY), '$CF_API_KEY').replace(str(spamwatch_api), '$spamwatch_api').replace(str(BACKUP_PASS), '$BACKUP_PASS'))
        logstxt.close()

    with open(logsname, "rb") as f:
        context.bot.send_document(document=f, filename=f.name, chat_id=user.id)


@kigcmd(command='updates')
@dev_plus
def updates_log(update: Update, context: CallbackContext):
    user = update.effective_user

    if not os.path.exists('updates.txt'):
        update.effective_message.reply_text("File doesn't exist")
        return
    updatesname = f"{dispatcher.bot.username}_updates.txt"

    # https://pythonexamples.org/python-replace-string-in-file/
    updatestxt = open("updates.txt", "rt")
    with open(updatesname, "wt") as updatesout:
        for line in updatestxt:
            updatesout.write(line.replace(str(DB_URI), '$DATABASE').replace(str(TOKEN), '$TOKEN').replace(str(APP_ID), '$APP_ID').replace(str(API_HASH), '$API_HASH').replace(str(CASH_API_KEY), '$CASH_API_KEY').replace(str(TIME_API_KEY), '$TIME_API_KEY').replace(str(LASTFM_API_KEY), '$LASTFM_API_KEY').replace(str(CF_API_KEY), '$CF_API_KEY').replace(str(spamwatch_api), '$spamwatch_api').replace(str(BACKUP_PASS), '$BACKUP_PASS'))
        updatestxt.close()

    with open(updatesname, "rb") as f:

        context.bot.send_document(document=f, filename=f.name, chat_id=user.id)


__mod_name__ = "Debug"
