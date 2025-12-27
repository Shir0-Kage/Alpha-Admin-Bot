from telebot import TeleBot
import utils
import gsheet_db_func
from paradestate_func import get_paradestate

BOT_TOKEN = ""

bot = TeleBot(BOT_TOKEN)

CHAT_ID = {}

def send_paradestate(chat):
    paradestate = get_paradestate()
    chat_id = CHAT_ID[chat]["CHAT_ID"]
    message_thread_id = CHAT_ID[chat]["THREAD_ID"]
    if len(paradestate) > 4095:
        for x in range(0, len(paradestate), 4095):
            bot.send_message(chat_id=chat_id,message_thread_id=message_thread_id,text=paradestate[x:x+4095])
    else:
        bot.send_message(chat_id=chat_id,message_thread_id=message_thread_id,text=paradestate)

def send_reminder(chat):
    chat_id = CHAT_ID[chat]["CHAT_ID"]
    message_thread_id = CHAT_ID[chat]["THREAD_ID"]
    bot.send_message(chat_id=chat_id,message_thread_id=message_thread_id,text="Reminder to Send paradestate to HQ")

def send_ha_alert(chat, msg):
    chat_id = CHAT_ID[chat]["CHAT_ID"]
    message_thread_id = CHAT_ID[chat]["THREAD_ID"]
    bot.send_message(chat_id=chat_id,message_thread_id=message_thread_id,text=msg)
