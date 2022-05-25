import html

from telegram import Update, TelegramError
from telegram.ext import CallbackContext
from telegram.ext.filters import Filters

from .helper_funcs.chat_status import connection_status
from .helper_funcs.decorators import kigcmd, kigmsg
from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_is_admin,
    u_na_errmsg
)
import tg_bot.modules.sql.antilinkedchannel_sql as sql
from .. import spamcheck

# TODO: Add logging


@kigcmd(command="cleanlinked", group=112)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check()
def set_antilinkedchannel(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    if len(args) > 0:
        if not user_is_admin(update, user.id, perm = AdminPerms.CAN_CHANGE_INFO):
            message.reply_text("You don't have enough rights!")
            return u_na_errmsg(message, AdminPerms.CAN_CHANGE_INFO)

        s = args[0].lower()
        if s in ["yes", "on"]:
            if sql.status_pin(chat.id):
                sql.disable_pin(chat.id)
                sql.enable_linked(chat.id)
                message.reply_html(
                    f"Enabled CleanLinked and Disabled anti channel pin in {html.escape(chat.title)}"
                )

            else:
                sql.enable_linked(chat.id)
                message.reply_html(f"Enabled anti linked channel in {html.escape(chat.title)}")
        elif s in ["off", "no"]:
            sql.disable_linked(chat.id)
            message.reply_html(
                f"Disabled anti linked channel in {html.escape(chat.title)}"
            )

        else:
            message.reply_text(f"Unrecognized arguments {s}")
        return

    message.reply_html(
        f"Linked channel deletion is currently {sql.status_linked(chat.id)} in {html.escape(chat.title)}"
    )


@kigmsg(Filters.is_automatic_forward, group=111)
def eliminate_linked_channel_msg(update: Update, _: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    if not sql.status_linked(chat.id):
        return
    try:
        message.delete()
    except TelegramError:
        sql.disable_linked(chat.id)
        message.reply_text(
            "I can't delete messages here, give me permissions first! Until then, I'll disable cleanlinked."
        )
        return


@kigcmd(command="antichannelpin", group=114)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check()
def set_antipinchannel(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user = update.effective_user

    if len(args) > 0:
        if not user_is_admin(update, user.id, perm = AdminPerms.CAN_CHANGE_INFO):
            message.reply_text("You don't have enough rights!")
            return u_na_errmsg(message, AdminPerms.CAN_CHANGE_INFO)

        s = args[0].lower()
        if s in ["yes", "on"]:
            if sql.status_linked(chat.id):
                sql.disable_linked(chat.id)
                sql.enable_pin(chat.id)
                message.reply_html(
                    f"Disabled CleanLinked and Enabled anti channel pin in {html.escape(chat.title)}"
                )

            else:
                sql.enable_pin(chat.id)
                message.reply_html(f"Enabled anti channel pin in {html.escape(chat.title)}")
        elif s in ["off", "no"]:
            sql.disable_pin(chat.id)
            message.reply_html(f"Disabled anti channel pin in {html.escape(chat.title)}")
        else:
            message.reply_text(f"Unrecognized arguments {s}")
        return

    message.reply_html(
        f"Linked channel message unpin is currently {sql.status_pin(chat.id)} in {html.escape(chat.title)}"
    )


@kigmsg(Filters.is_automatic_forward | Filters.status_update.pinned_message, group=113)
def eliminate_linked_channel_msg(update: Update, _: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    if not sql.status_pin(chat.id):
        return

    try:
        message.unpin()
    except TelegramError:
        sql.disable_pin(chat.id)
        message.reply_text(
            "I can't delete messages here, give me permissions first! Until then, I'll disable cleanlinked."
        )
        return
