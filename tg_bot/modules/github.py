# from AstrakoBot
import html
from typing import Optional, List

import tg_bot.modules.helper_funcs.git_api as api
import tg_bot.modules.sql.github_sql as sql

from .sql.clear_cmd_sql import get_clearcmd
from tg_bot import dispatcher, spamcheck
from .helper_funcs.misc import delete
from .disable import DisableAbleCommandHandler

from telegram.ext import (
    CallbackContext,
    CommandHandler,
)

from telegram import (
    Update,
    ParseMode,
)

# @spamcheck
def getphh(index):
    recentRelease = api.getReleaseData(api.getData("phhusson/treble_experimentations"), index)
    if recentRelease is None:
        return "The specified release could not be found"
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "<b>Author:</b> <a href='{}'>{}</a>\n".format(authorUrl, author)
    message += f"<b>Release Name:</b> <code>{releaseName}" + "</code>\n\n"
    message += "<b>Assets:</b>\n"
    for asset in assets:
        fileName = api.getReleaseFileName(asset)
        if fileName in ("manifest.xml", "patches.zip"):
            continue
        fileURL = api.getReleaseFileURL(asset)
        assetFile = f"• <a href='{fileURL}'>{fileName}</a>"
        sizeB = ((api.getSize(asset))/1024)/1024
        size = "{0:.2f}".format(sizeB)
        message += assetFile + "\n"
        message += f"    <code>Size: {size}" + " MB</code>\n"
    return message

# @spamcheck
# do not async
def getData(url, index):
    if not api.getData(url):
        return "Invalid <user>/<repo> combo"
    recentRelease = api.getReleaseData(api.getData(url), index)
    if recentRelease is None:
        return "The specified release could not be found"
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "*Author:* [{}]({})\n".format(author, authorUrl)
    message += f"*Release Name:* {releaseName}" + "\n\n"
    for asset in assets:
        message += "*Asset:* \n"
        fileName = api.getReleaseFileName(asset)
        fileURL = api.getReleaseFileURL(asset)
        assetFile = f"[{fileName}]({fileURL})"
        sizeB = ((api.getSize(asset)) / 1024) / 1024
        size = "{0:.2f}".format(sizeB)
        downloadCount = api.getDownloadCount(asset)
        message += assetFile + "\n"
        message += f"Size: {size} MB"
        message += "\nDownload Count: " + str(downloadCount) + "\n\n"
    return message

@spamcheck
def getRepo(bot, update, reponame):
    chat_id = update.effective_chat.id
    if repo := sql.get_repo(str(chat_id), reponame):
        return repo.value, repo.backoffset
    return None, None

@spamcheck
def getRelease(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if len(args) == 0:
        msg.reply_text("Please use some arguments!")
        return
    if (
        len(args) != 1
        and (len(args) != 2 or not args[1].isdigit())
        and "/" not in args[0]
    ):
        deletion(update, context, msg.reply_text("Please specify a valid combination of <user>/<repo>"))
        return
    index = int(args[1]) if len(args) == 2 else 0
    url = args[0]
    text = getData(url, index)
    deletion(update, context, msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True))
    return

# @spamcheck
# def hashFetch(update: Update, context: CallbackContext):  # kanged from notes
#     bot, args = context.bot, context.args
#     message = update.effective_message.text
#     msg = update.effective_message
#     fst_word = message.split()[0]
#     no_hash = fst_word[1:]
#     url, index = getRepo(bot, update, no_hash)
#     if url is None and index is None:
#         deletion(update, context, msg.reply_text(
#             "There was a problem parsing your request. Likely this is not a saved repo shortcut",
#             parse_mode=ParseMode.MARKDOWN,
#             disable_web_page_preview=True,
#         ))
#         return
#     text = getData(url, index)
#     deletion(update, context, msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True))
#     return

@spamcheck
def cmdFetch(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if len(args) != 1:
        deletion(update, context, msg.reply_text("Invalid repo name"))
        return
    url, index = getRepo(bot, update, args[0])
    if url is None and index is None:
        deletion(update, context, msg.reply_text(
            "There was a problem parsing your request. Likely this is not a saved repo shortcut",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        ))
        return
    text = getData(url, index)
    deletion(update, context, msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True))
    return

@spamcheck
def changelog(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    msg = update.effective_message
    if len(args) != 1:
        deletion(update, context, msg.reply_text("Invalid repo name"))
        return
    url, index = getRepo(bot, update, args[0])
    if not api.getData(url):
        msg.reply_text("Invalid <user>/<repo> combo")
        return
    data = api.getData(url)
    release = api.getReleaseData(data, index)
    body = api.getBody(release)
    deletion(update, context, msg.reply_text(body))
    return

# @spamcheck
# @user_admin
# def saveRepo(update: Update, context: CallbackContext):
#     bot, args = context.bot, context.args
#     chat_id = update.effective_chat.id
#     msg = update.effective_message
#     if (
#         len(args) != 2
#         and (len(args) != 3 and not args[2].isdigit())
#         or not ("/" in args[1])
#     ):
#         deletion(update, context, msg.reply_text("Invalid data, use <reponame> <user>/<repo> <value (optional)>"))
#         return
#     index = 0
#     if len(args) == 3:
#         index = int(args[2])
#     sql.add_repo_to_db(str(chat_id), args[0], args[1], index)
#     deletion(update, context, msg.reply_text("Repo shortcut saved successfully!"))
#     return

# @spamcheck
# @user_admin
# def delRepo(update: Update, context: CallbackContext):
#     bot, args = context.bot, context.args
#     chat_id = update.effective_chat.id
#     msg = update.effective_message
#     if len(args) != 1:
#         msg.reply_text("Invalid repo name!")
#         return
#     sql.rm_repo(str(chat_id), args[0])
#     deletion(update, context, msg.reply_text("Repo shortcut deleted successfully!"))
#     return

# @spamcheck
# def listRepo(update: Update, context: CallbackContext):
#     chat_id = update.effective_chat.id
#     chat = update.effective_chat
#     chat_name = chat.title or chat.first_name or chat.username
#     repo_list = sql.get_all_repos(str(chat_id))
#     msg = "*List of repo shotcuts in {}:*\n"
#     des = "You can get repo shortcuts by using `/fetch repo`, or `&repo`.\n"
#     for repo in repo_list:
#         repo_name = " • `{}`\n".format(repo.name)
#         if len(msg) + len(repo_name) > MAX_MESSAGE_LENGTH:
#             deletion(update, context, update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN))
#             msg = ""
#         msg += repo_name
#     if msg == "*List of repo shotcuts in {}:*\n":
#         deletion(update, context, update.effective_message.reply_text("No repo shortcuts in this chat!"))
#     elif len(msg) != 0:
#         deletion(update, context, update.effective_message.reply_text(
#             msg.format(chat_name) + des, parse_mode=ParseMode.MARKDOWN
#         ))

@spamcheck
def getVer(update: Update, context: CallbackContext):
    msg = update.effective_message
    ver = api.vercheck()
    deletion(update, context, msg.reply_text(f"GitHub API version: {ver}"))
    return


def deletion(update: Update, context: CallbackContext, delmsg):
    chat = update.effective_chat
    if cleartime := get_clearcmd(chat.id, "github"):
        context.dispatcher.run_async(delete, delmsg, cleartime.time)





RELEASE_HANDLER = DisableAbleCommandHandler(
    "git", getRelease, admin_ok=True, run_async=True
)
FETCH_HANDLER = DisableAbleCommandHandler(
    "fetch", cmdFetch, admin_ok=True, run_async=True
)
# SAVEREPO_HANDLER = CommandHandler("saverepo", saveRepo, run_async=True)
# DELREPO_HANDLER = CommandHandler("delrepo", delRepo, run_async=True)
# LISTREPO_HANDLER = DisableAbleCommandHandler("listrepo", listRepo, admin_ok=True, run_async=True)
VERCHECKER_HANDLER = DisableAbleCommandHandler("gitver", getVer, admin_ok=True, run_async=True)
CHANGELOG_HANDLER = DisableAbleCommandHandler(
    "changelog", changelog, admin_ok=True, run_async=True
)

# HASHFETCH_HANDLER = MessageHandler(Filters.regex(r"^&[^\s]+"), hashFetch)


dispatcher.add_handler(RELEASE_HANDLER)
dispatcher.add_handler(FETCH_HANDLER)
# dispatcher.add_handler(SAVEREPO_HANDLER)
# dispatcher.add_handler(DELREPO_HANDLER)
# dispatcher.add_handler(LISTREPO_HANDLER)
# dispatcher.add_handler(HASHFETCH_HANDLER)
dispatcher.add_handler(VERCHECKER_HANDLER)
dispatcher.add_handler(CHANGELOG_HANDLER)


from .language import gs

def get_help(chat):
    return gs(chat, "github_help")

__mod_name__ = "Github"