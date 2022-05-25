import html
import re
from telegram import ChatPermissions, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, Filters
from telegram.utils.helpers import mention_html
import tg_bot.modules.sql.blacklist_sql as sql
from .. import SUDO_USERS, log, spamcheck
from .sql.approve_sql import is_approved
from .helper_funcs.chat_status import connection_status
from .helper_funcs.extraction import extract_text
from .helper_funcs.misc import split_message
from .log_channel import loggable
from .warns import warn
from .helper_funcs.string_handling import extract_time
from .helper_funcs.decorators import kigcmd, kigmsg, kigcallback
from .helper_funcs.alternate import send_message, typing_action

from .helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_not_admin_check,
)

BLACKLIST_GROUP = -3

@kigcmd(command=["blacklist", "blacklists", "blocklist", "blocklists"], pass_args=True, admin_ok=True)
@spamcheck
@user_admin_check()
@typing_action
def blacklist(update, context):
    chat = update.effective_chat
    user = update.effective_user
    args = context.args


    filter_list = "<b>Blacklist settings for :{}</b>:\n".format(chat.title)

    getmode, getvalue = sql.get_blacklist_setting(chat.id)
    if getmode == 0:
        settypeblacklist = "Do nothing"
    elif getmode == 1:
        settypeblacklist = "Delete"
    elif getmode == 2:
        settypeblacklist = "Warn"
    elif getmode == 3:
        settypeblacklist = "Mute"
    elif getmode == 4:
        settypeblacklist = "Kick"
    elif getmode == 5:
        settypeblacklist = "Ban"
    elif getmode == 6:
        settypeblacklist = f"Temporarily Ban for {getvalue}"
    elif getmode == 7:
        settypeblacklist = f"Temporarily Mute for {getvalue}"

    filter_list += "ㅤ<b>Current blacklistmode:</b>\nㅤㅤ<b>{}</b>.\n".format(settypeblacklist)

    filter_list += "ㅤ<b>Current blacklisted words:</b>\n"

    all_blacklisted = sql.get_chat_blacklist(chat.id)

    actions = {
        0: "default",
        1: "delete",
        2: "warn",
        3: "mute",
        4: "kick",
        5: "ban",
    }
    if len(args) > 0 and args[0].lower() == "copy":
        for x in all_blacklisted:

            trigger = x[0]
            # print(trigger)
            act = x[1]
            # print(act)

            action = actions[act]

            filter_list += "ㅤ <code>{}</code>\nㅤㅤ  <b>Action:</b> {}\n".format(html.escape(trigger), action)
    else:
        for x in all_blacklisted:

            trigger = x[0]
            # print(trigger)
            act = x[1]
            # print(act)

            action = actions[act]

            # filter_list += "ㅤㅤ<code>{}</code>\nㅤㅤㅤ<b>Action:</b> {}\n".format(html.escape(trigger), action)
            filter_list += "ㅤㅤ- <code>{}</code>\nㅤㅤㅤ  <b>Action:</b> {}\n".format(html.escape(trigger), action)

    # for trigger in all_blacklisted:
    #     filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(filter_list)
    for text in split_text:
        if len(all_blacklisted) == 0:
            send_message(
                update.effective_message,
                f"No blacklisted words in <b>{chat.title}</b>!",
                parse_mode=ParseMode.HTML,
            )

            return
        send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@kigcmd(command=["addblacklist", "addblocklist"], pass_args=True)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@typing_action
def add_blacklist(update, _):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)

    chat_name = html.escape(chat.title)

    if len(words) > 1:
        text = words[1]
        to_blacklist = list(
            {
                trigger.strip()
                for trigger in text.split("\n")
                if trigger.strip()
            }
        )
        erroract = []

        # import re
        for trigger in to_blacklist:
            if trigger.find(r" \{\w*\}") != -1:
                # print("aa")
                # print(trigger)
                sql.add_to_blacklist(chat.id, trigger.lower(), 0)
                act = "default"
            else:

                # print("bb")
                # print(trigger)
                trg = trigger.split(" {")[0]
                # trg = re.split(r" \{\w*\}", trigger)
                # print(trg)
                try:
                    act = trigger.split(" {")[1].replace("}", "")
                except IndexError:
                    act = "default"
                # act = str(re.split(r" \{\w*\}", trigger)[1]).replace(" ", "").replace("{", "").replace("}", "")
                # print(act)

                actions = {"delete", "warn", "mute", "kick", "ban"}

                if act in actions:
                    actionz = {
                        "delete": 1,
                        "warn": 2,
                        "mute": 3,
                        "kick": 4,
                        "ban": 5,
                    }
                    action = actionz[act]


                    # blacklist = "{}, {}".format(, action)

                    sql.add_to_blacklist(chat.id, trg.lower(), action)

                else:
                    # blacklist = "{}, 0".format()
                    sql.add_to_blacklist(chat.id, trg.lower(), 0)
                    erroract.append(act)

        if len(to_blacklist) == 1:

            reply = "Added blacklist trigger: <code>{}</code> with <b>{}</b> action!"
            send_message(
                update.effective_message,
                reply.format(
                    html.escape(trg), act
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            reply = "Added blacklist <code>{}</code> in chat: <b>{}</b>!"
            if len(erroract) > 1:
                errstr = f"\nUnknown action(s): ({erroract})\\\x1f                            \nThe possible actions are:\\\x1f                            \n{str(actions)}"

                reply += errstr
            send_message(
                update.effective_message,
                reply.format(
                    len(to_blacklist), chat_name
                ),
                parse_mode=ParseMode.HTML,
            )


    else:
        send_message(
            update.effective_message,
            "Tell me which words you would like to add in blacklist.",
        )

@kigcmd(command=["unblacklist", "unblocklist"], pass_args=True)
@spamcheck
@typing_action
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def unblacklist(update, _):
    msg = update.effective_message
    chat = update.effective_chat
    words = msg.text.split(None, 1)

    chat_id = chat.id
    chat_name = html.escape(chat.title)

    if len(words) > 1:
        text = words[1]
        to_unblacklist = list(
            {
                trigger.strip()
                for trigger in text.split("\n")
                if trigger.strip()
            }
        )

        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                send_message(
                    update.effective_message,
                    f"Removed <code>{html.escape(to_unblacklist[0])}</code> from blacklist in <b>{chat_name}</b>!",
                    parse_mode=ParseMode.HTML,
                )

            else:
                send_message(
                    update.effective_message, "This is not a blacklist trigger!"
                )

        elif successful == len(to_unblacklist):
            send_message(
                update.effective_message,
                f"Removed <code>{successful}</code> from blacklist in <b>{chat_name}</b>!",
                parse_mode=ParseMode.HTML,
            )


        elif not successful:
            send_message(
                update.effective_message,
                "None of these triggers exist so it can't be removed.".format(
                    successful, len(to_unblacklist) - successful
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                update.effective_message,
                f"Removed <code>{successful}</code> from blacklist. {len(to_unblacklist) - successful} did not exist, so were not removed.",
                parse_mode=ParseMode.HTML,
            )

    else:
        send_message(
            update.effective_message,
            "Tell me which words you would like to remove from blacklist!",
        )

@kigcmd(command=["blacklistmode", "blocklistmode"], pass_args=True)
@spamcheck
@typing_action
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
def blacklist_mode(update, context):  # sourcery no-metrics
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    chat_id = chat.id
    chat_name = html.escape(chat.title)

    if args:
        if args[0].lower() in ["off", "nothing", "no"]:
            settypeblacklist = "do nothing"
            sql.set_blacklist_strength(chat_id, 0, "0")
        elif args[0].lower() in ["del", "delete"]:
            settypeblacklist = "will delete blacklisted message"
            sql.set_blacklist_strength(chat_id, 1, "0")
        elif args[0].lower() == "warn":
            settypeblacklist = "warn the sender"
            sql.set_blacklist_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeblacklist = "mute the sender"
            sql.set_blacklist_strength(chat_id, 3, "0")
        elif args[0].lower() == "kick":
            settypeblacklist = "kick the sender"
            sql.set_blacklist_strength(chat_id, 4, "0")
        elif args[0].lower() == "ban":
            settypeblacklist = "ban the sender"
            sql.set_blacklist_strength(chat_id, 5, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for blacklist but you didn't specified time; Try, `/blacklistmode tban <timevalue>`.

Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """Invalid time value!
Example of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            settypeblacklist = f"temporarily ban for {args[1]}"
            sql.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for blacklist but you didn't specified  time; try, `/blacklistmode tmute <timevalue>`.

Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = """Invalid time value!
Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return ""
            settypeblacklist = f"temporarily mute for {args[1]}"
            sql.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            send_message(
                update.effective_message,
                "I only understand: off/del/warn/ban/kick/mute/tban/tmute!",
            )
            return ""
        text = f"Changed blacklist mode: `{settypeblacklist}`!"
        send_message(update.effective_message, text, parse_mode="markdown")
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Changed the blacklist mode. will {}.".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                settypeblacklist,
            )
        )
    else:
        getmode, getvalue = sql.get_blacklist_setting(chat.id)
        if getmode == 0:
            settypeblacklist = "do nothing"
        elif getmode == 1:
            settypeblacklist = "delete"
        elif getmode == 2:
            settypeblacklist = "warn"
        elif getmode == 3:
            settypeblacklist = "mute"
        elif getmode == 4:
            settypeblacklist = "kick"
        elif getmode == 5:
            settypeblacklist = "ban"
        elif getmode == 6:
            settypeblacklist = f"temporarily ban for {getvalue}"
        elif getmode == 7:
            settypeblacklist = f"temporarily mute for {getvalue}"
        text = f"Current blacklistmode: *{settypeblacklist}*."
        send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
    return ""


def findall(p, s):
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i + 1)



@kigmsg(((Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.chat_type.groups), group=BLACKLIST_GROUP)
@user_not_admin_check
def del_blacklist(update: Update, context: CallbackContext):  # sourcery no-metrics
    chat = update.effective_chat
    message = update.effective_message
    user = message.sender_chat or update.effective_user
    bot = context.bot
    to_match = extract_text(message)
    # print("to_match")
    # print(to_match)
    if not to_match:
        return
    if is_approved(chat.id, user.id):
        return
    getmode, value = sql.get_blacklist_setting(chat.id)

    chat_filters = sql.get_chat_blacklist(chat.id)
    # print("all blll ----------------------") 
    # print(chat_filters) 

    for tuptrigger in chat_filters:
        # print(type(tuptrigger))
        trigger = str(tuptrigger[0])
        getmode = (int(tuptrigger[1]) if int(tuptrigger[1]) > 0 else getmode)
        # print("trigger  " + str(trigger) + "  mode  " + str(getmode))
        # print(trigger)
        # print(getmode)
        pattern = r"( |^|[^\w])" + re.escape(trigger) + r"( |$|[^\w])"
        # print(pattern)
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                if getmode == 0:
                    return
                elif getmode == 1:
                    message.delete()
                elif getmode == 2:
                    message.delete()
                    warn(
                        update.effective_user,
                        update,
                        f"Using blacklisted trigger: {trigger}",
                        message,
                        update.effective_user,
                    )

                    return
                elif getmode == 3:
                    message.delete()
                    bot.restrict_chat_member(
                        chat.id,
                        update.effective_user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    bot.sendMessage(
                        chat.id,
                        f"Muted {user.first_name} for using Blacklisted word: {trigger}!",
                    )
                    return
                elif getmode == 4:
                    message.delete()
                    if res := chat.unban_member(update.effective_user.id):
                        bot.sendMessage(
                            chat.id,
                            f"Kicked {user.first_name} for using Blacklisted word: {trigger}!",
                        )
                    return
                elif getmode == 5:
                    message.delete()
                    chat.ban_member(user.id)
                    bot.sendMessage(
                        chat.id,
                        f"Banned {user.first_name} for using Blacklisted word: {trigger}",
                    )
                    return
                elif getmode == 6:
                    message.delete()
                    bantime = extract_time(message, value)
                    chat.ban_member(user.id, until_date=bantime)
                    bot.sendMessage(
                        chat.id,
                        f"Banned {user.first_name} until '{value}' for using Blacklisted word: {trigger}!",
                    )
                    return
                elif getmode == 7:
                    message.delete()
                    mutetime = extract_time(message, value)
                    bot.restrict_chat_member(
                        chat.id,
                        user.id,
                        until_date=mutetime,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    bot.sendMessage(
                        chat.id,
                        f"Muted {user.first_name} until '{value}' for using Blacklisted word: {trigger}!",
                    )
                    return
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    log.exception("Error while deleting blacklist message.")
            break

from telegram import ParseMode, InlineKeyboardMarkup, Message, InlineKeyboardButton

@kigcmd(command=["removeallblacklists", "removeallblocklists"], filters=Filters.chat_type.groups)
@spamcheck
def rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        update.effective_message.reply_text(
            "Only the chat owner can clear all blacklists at once."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Remove all Blacklists", callback_data="blacklists_rmall"
                    )
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="blacklists_cancel")],
            ]
        )
        update.effective_message.reply_text(
            f"Are you sure you would like to stop ALL blacklists in {chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )

@kigcallback(pattern=r"blacklists_.*")
@loggable
def rmall_callback(update, context) -> str:
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    member = chat.get_member(query.from_user.id)
    user = query.from_user
    if query.data == "blacklists_rmall":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            allfilters = sql.get_chat_blacklist(chat.id)
            if not allfilters:
                msg.edit_text("No blacklists in this chat, nothing to stop!")
                return ""

            count = 0
            filterlist = []
            for x in allfilters:
                count += 1
                filterlist.append(x)
            print(filterlist)
            for i in filterlist:
                sql.rm_from_blacklist(chat.id, i[0])

            msg.edit_text(f"Cleaned {count} bl in {chat.title}")

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#CLEAREDALLBLACKLISTS\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
            )
            return log_message

        if member.status == "administrator":
            query.answer("Only owner of the chat can do this.")
            return ""

        if member.status == "member":
            query.answer("You need to be admin to do this.")
            return ""
    elif query.data == "blacklists_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            msg.edit_text("Clearing of all filters has been cancelled.")
            return ""
        if member.status == "administrator":
            query.answer("Only owner of the chat can do this.")
            return ""
        if member.status == "member":
            query.answer("You need to be admin to do this.")
            return ""


def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get("blacklist", {})
    for trigger in blacklist:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return f"There are {blacklisted} blacklisted words."


def __stats__():
    return f"• {sql.num_blacklist_filters()} blacklist triggers, across {sql.num_blacklist_filter_chats()} chats."


__mod_name__ = "Blacklists"

from .language import gs

def get_help(chat):
    return gs(chat, "blacklist_help")
