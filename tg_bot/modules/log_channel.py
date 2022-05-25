from datetime import datetime
from functools import wraps
from tg_bot import OWNER_ID, spamcheck

from telegram.ext import CallbackContext
from .helper_funcs.decorators import kigcmd, kigcallback
from .helper_funcs.misc import is_module_loaded
from .language import gs
from telegram.error import Unauthorized
from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
    bot_is_admin,
    user_is_admin,
    user_not_admin_check,
)


def get_help(chat):
    return gs(chat, "log_help")


FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram import ParseMode, Update, InlineKeyboardMarkup, InlineKeyboardButton
    from telegram.error import BadRequest, Unauthorized
    from telegram.utils.helpers import escape_markdown

    from tg_bot import GBAN_LOGS, log, dispatcher
    from .sql import log_channel_sql as sql
 

    def loggable(func):
        @wraps(func)
        def log_action(update, context, *args, **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat  # type: Optional[Chat]
            message = update.effective_message  # type: Optional[Message]

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += f"\n<b>Event Stamp</b>: <code>{datetime.utcnow().strftime(datetime_fmt)}</code>"

                try:
                    if message.chat.type == chat.SUPERGROUP:
                        if message.chat.username:
                            result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                        else:
                            cid = str(chat.id).replace("-100", '')
                            result += f'\n<b>Link:</b> <a href="https://t.me/c/{cid}/{message.message_id}">click here</a>'
                except AttributeError:
                    result += '\n<b>Link:</b> No link for manual actions.'
                if log_chat := sql.get_chat_log_channel(chat.id):
                    send_log(context, log_chat, chat.id, result)

            return result

        return log_action


    def gloggable(func):
        @wraps(func)
        def glog_action(update, context, *args, **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat  # type: Optional[Chat]
            message = update.effective_message  # type: Optional[Message]

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += "\n<b>Event Stamp</b>: <code>{}</code>".format(
                    datetime.utcnow().strftime(datetime_fmt)
                )

                if message.chat.type == chat.SUPERGROUP:
                    if message.chat.username:
                        result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                    else:
                        cid = str(chat.id).replace("-100", '')
                        result += f'\n<b>Link:</b> <a href="https://t.me/c/{cid}/{message.message_id}">click here</a>'
                if log_chat := GBAN_LOGS or OWNER_ID:
                    send_log(context, log_chat, chat.id, result)

            return result

        return glog_action


    def send_log(
            context: CallbackContext, log_chat_id: str, orig_chat_id: str, result: str
    ):
        bot = context.bot
        try:
            bot.send_message(
                log_chat_id,
                result,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message == "Chat not found":
                bot.send_message(
                    orig_chat_id, "This log channel has been deleted - unsetting."
                )
                sql.stop_chat_logging(orig_chat_id)
            else:
                log.warning(excp.message)
                log.warning(result)
                log.exception("Could not parse")

                bot.send_message(
                    log_chat_id,
                    result
                    + "\n\nFormatting has been disabled due to an unexpected error.",
                )
        except Unauthorized as excp:
            if excp.message == "bot is not a member of the channel chat":
                bot.send_message(
                    orig_chat_id, "I don't have access to the log channel - unsetting."
                )
                sql.stop_chat_logging(orig_chat_id)


    @kigcmd(command='logchannel')
    @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @spamcheck
    def logging(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        if log_channel := sql.get_chat_log_channel(chat.id):
            log_channel_info = bot.get_chat(log_channel)
            message.reply_text(
                f"This group has all it's logs sent to:"
                f" {escape_markdown(log_channel_info.title)} (`{log_channel}`)",
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            message.reply_text("No log channel has been set for this group!")


    @kigcmd(command='setlog')
    @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @spamcheck
    def setlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat
        if chat.type == chat.CHANNEL:
            message.reply_text(
                "Now, forward the /setlog to the group you want to tie this channel to!"
            )

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                message.delete()
            except BadRequest as excp:
                if excp.message != 'Message to delete not found':
                    log.exception(
                        'Error deleting message in log channel. Should work anyway though.'
                    )

            try:
                bot.send_message(
                    message.forward_from_chat.id,
                    f"This channel has been set as the log channel for {chat.title or chat.first_name}.",
                )
            except Unauthorized as excp:
                if excp.message == "Forbidden: bot is not a member of the channel chat":
                    bot.send_message(chat.id, "Successfully set log channel!")
                else:
                    log.exception("ERROR in setting the log channel.")

            bot.send_message(chat.id, "Successfully set log channel!")

        else:
            message.reply_text(
                "The steps to set a log channel are:\n"
                " - add bot to the desired channel\n"
                " - send /setlog to the channel\n"
                " - forward the /setlog to the group\n"
            )


    @kigcmd(command='unsetlog')
    @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @spamcheck
    def unsetlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        if log_channel := sql.stop_chat_logging(chat.id):
            bot.send_message(
                log_channel, f"Channel has been unlinked from {chat.title}"
            )
            message.reply_text("Log channel has been un-set.")

        else:
            message.reply_text("No log channel has been set yet!")


    def __stats__():
        return f"• {sql.num_logchannels()} log channels set."


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id, user_id):
        if log_channel := sql.get_chat_log_channel(chat_id):
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return f"This group has all it's logs sent to: {escape_markdown(log_channel_info.title)} (`{log_channel}`)"
        return "No log channel is set for this group!"


    __help__ = """
*Admins only:*
• `/logchannel`*:* get log channel info
• `/setlog`*:* set the log channel.
• `/unsetlog`*:* unset the log channel.

Setting the log channel is done by:
• adding the bot to the desired channel (as an admin!)
• sending `/setlog` in the channel
• forwarding the `/setlog` to the group
"""

    __mod_name__ = "Logger"

else:
    # run anyway if module not loaded
    def loggable(func):
        return func


    def gloggable(func):
        return func


@kigcmd("logsettings")
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def log_settings(update: Update, _: CallbackContext):
    chat = update.effective_chat
    chat_set = sql.get_chat_setting(chat_id=chat.id)
    message = update.effective_message
    user = update.effective_user
    if not chat_set:
        sql.set_chat_setting(setting=sql.LogChannelSettings(chat.id, True, True, True, True, True))
    btn = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="Warn", callback_data="log_tog_warn"),
                InlineKeyboardButton(text="Action", callback_data="log_tog_act")
            ],
            [
                InlineKeyboardButton(text="Join", callback_data="log_tog_join"),
                InlineKeyboardButton(text="Leave", callback_data="log_tog_leave")
            ],
            [
                InlineKeyboardButton(text="Report", callback_data="log_tog_rep")
            ]
        ]
    )
    msg = update.effective_message
    msg.reply_text("Toggle channel log settings", reply_markup=btn)


from .sql import log_channel_sql as sql


@kigcallback(pattern=r"log_tog_.*")
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, noreply=True)
def log_setting_callback(update: Update, context: CallbackContext):
    cb = update.callback_query
    user = cb.from_user
    chat = cb.message.chat
    setting = cb.data.replace("log_tog_", "")
    chat_set = sql.get_chat_setting(chat_id=chat.id)
    if not chat_set:
        sql.set_chat_setting(setting=sql.LogChannelSettings(chat.id, True, True, True, True, True))

    t = sql.get_chat_setting(chat.id)
    if setting == "warn":
        r = t.toggle_warn()
        cb.answer(f"Warning log set to {r}")
        return
    if setting == "act":
        r = t.toggle_action()
        cb.answer(f"Action log set to {r}")
        return
    if setting == "join":
        r = t.toggle_joins()
        cb.answer(f"Join log set to {r}")
        return
    if setting == "leave":
        r = t.toggle_leave()
        cb.answer(f"Leave log set to {r}")
        return
    if setting == "rep":
        r = t.toggle_report()
        cb.answer(f"Report log set to {r}")
        return

    cb.answer("Idk what to do")
