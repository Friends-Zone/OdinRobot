import os
import subprocess

from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.filters import Filters


from telegram.update import Update

import datetime
from .. import DB_URI, OWNER_ID, SYS_ADMIN, dispatcher, log, BACKUP_PASS

from .helper_funcs.decorators import kigcmd
import shutil
from time import sleep




@kigcmd(command="backupdb", filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def backup_now(update: Update, context: CallbackContext):
    cronjob.run(dispatcher=dispatcher)

@kigcmd(command="jobs", filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def get_jobs(update: Update, context: CallbackContext):
    a = cronjob.job_queue.jobs().count(j)
    print(a)
    update.effective_message.reply_text(a)

@kigcmd(command="stopjobs", filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def stop_jobs(update: Update, context: CallbackContext):
    print(j.stop())
    update.effective_message.reply_text("Scheduler has been shut down")

@kigcmd(command="startjobs", filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def start_jobs(update: Update, context: CallbackContext):
    print(j.start())
    update.effective_message.reply_text("Scheduler started")

zip_pass = BACKUP_PASS

def backup_db(ctx: CallbackContext):
    bot = dispatcher.bot
    tmpmsg = "Performing backup, Please wait..."
    tmp = bot.send_message(OWNER_ID, tmpmsg)
    datenow = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dbbkpname = f"db_{bot.username}_{datenow}.tar"
    bkplocation = f"backups/{datenow}"
    bkpcmd = f"pg_dump {DB_URI} --format=tar > {bkplocation}/{dbbkpname}"

    if not os.path.exists(bkplocation):
        os.makedirs(bkplocation)
    log.info("performing db backup")
    loginfo = "db backup"
    term(bkpcmd, loginfo)
    if not os.path.exists(f'{bkplocation}/{dbbkpname}'):
        bot.send_message(OWNER_ID, "An error occurred during the db backup")
        tmp.edit_text("Backup Failed!")
        sleep(8)
        tmp.delete()
        return
    else:
        log.info("copying config, logs, and updates to backup location")
        if os.path.exists('logs.txt'):
            print("logs copied")
            shutil.copyfile('logs.txt', f'{bkplocation}/logs.txt')
        if os.path.exists('updates.txt'):
            print("updates copied")
            shutil.copyfile('updates.txt', f'{bkplocation}/updates.txt')
        if os.path.exists('config.ini'):
            print("config copied")
            shutil.copyfile('config.ini', f'{bkplocation}/config.ini')
        log.info("zipping the backup")
        zipcmd = f"zip --password '{zip_pass}' {bkplocation} {bkplocation}/*"
        zipinfo = "zipping db backup"
        log.info("zip intiated")
        term(zipcmd, zipinfo)
        log.info("zip done")
        sleep(1)
        with open(f'backups/{datenow}.zip', 'rb') as bkp:
            nm = "{} backup \n".format(bot.username) + datenow
            bot.send_document(OWNER_ID,
                              document=bkp,
                              caption=nm,
                              timeout=20
                              )
        log.info("removing zipped files")
        shutil.rmtree(f"backups/{datenow}")
        log.info("backup done")
        tmp.edit_text("Backup complete!")
        sleep(5)
        tmp.delete()


@kigcmd(command="purgebackups", filters=Filters.user(SYS_ADMIN) | Filters.user(OWNER_ID))
def stop_jobs(update: Update, context: CallbackContext):
    shutil.rmtree("backups")
    update.effective_message.reply_text("'backups' directory has been purged!")

def term(cmd, info):
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    stdout, stderr = process.communicate()
    stderr = stderr.decode()
    if stdout := stdout.decode():
        log.info(f"{info} successful!")
        log.info(f"{stdout}")
    if stderr:
        log.error(f"error while running {info}")
        log.info(f"{stderr}")


from tg_bot import updater as u
j = u.job_queue
twhen = datetime.datetime.strptime('01:00', '%H:%M').time()
cronjob = j.run_daily(callback=backup_db, name="database backups", time=twhen)

