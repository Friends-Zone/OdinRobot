from tg_bot import dispatcher, spamcheck
from telegram import Update
from telegram.ext import CallbackContext
from .helper_funcs.decorators import kigcmd

@kigcmd(command='shout')
@spamcheck
def shout(update: Update, context: CallbackContext):
    try:
        args = context.args
    except IndexError:
        return update.effective_message.reply_text("What do you want me to shout?", parse_mode="MARKDOWN")
    text = " ".join(args)
    result = [" ".join(list(text))]
    result.extend(
        f"{symbol} " + "  " * pos + symbol
        for pos, symbol in enumerate(text[1:])
    )

    result = list("\n".join(result))
    result[0] = text[0]
    result = "".join(result)
    msg = "```\n" + result + "```"
    return update.effective_message.reply_text(msg, parse_mode="MARKDOWN")
