from telebot import TeleBot
from paradestate_func import get_paradestate
from config import BOT_TOKEN, CHAT_ID

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")

bot = TeleBot(BOT_TOKEN)

MAX_MSG = 4095


def send_long_message(chat_id, message_thread_id, text):
    # telegram caps messages at 4096 chars, so split long ones
    if len(text) > MAX_MSG:
        for x in range(0, len(text), MAX_MSG):
            bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=text[x:x + MAX_MSG])
    else:
        bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=text)

def send_paradestate(chat):
    paradestate = get_paradestate()
    chat_id = CHAT_ID[chat]["CHAT_ID"]
    message_thread_id = CHAT_ID[chat]["THREAD_ID"]
    send_long_message(chat_id, message_thread_id, paradestate)

def send_reminder(chat):
    chat_id = CHAT_ID[chat]["CHAT_ID"]
    message_thread_id = CHAT_ID[chat]["THREAD_ID"]
    bot.send_message(chat_id=chat_id,message_thread_id=message_thread_id,text="Reminder to Send paradestate to HQ")

def send_ha_alert(chat, msg):
    chat_id = CHAT_ID[chat]["CHAT_ID"]
    message_thread_id = CHAT_ID[chat]["THREAD_ID"]
    bot.send_message(chat_id=chat_id,message_thread_id=message_thread_id,text=msg)
