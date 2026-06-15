from telegrambot import bot, CHAT_ID
import random
from config import SERVICE_ACCOUNT, PARADESTATE_SHEET_URL, BOT_UPDATES_CHAT, validate_config, setup_logging
import utils

setup_logging()
validate_config()

gc = SERVICE_ACCOUNT
sh = gc.open_by_url(PARADESTATE_SHEET_URL)
worksheet = sh.get_worksheet(0)

now = utils.get_now()
current_hour = now.hour
A1col, col = utils.get_today_col(worksheet,now)
today_activity = worksheet.col_values(col)[2]

reminder_hours = [10, 14, 17]
if "MOVEMENT" in today_activity and current_hour in reminder_hours:
    chat_id = CHAT_ID[BOT_UPDATES_CHAT]["CHAT_ID"]
    message_thread_id = CHAT_ID[BOT_UPDATES_CHAT]["THREAD_ID"]

    reminder = "Remember to do daily 30s"

    time_key = int(now.strftime("%Y%m%d%H%M%S"))
    

    bot.send_message(chat_id=chat_id, message_thread_id=message_thread_id, text=reminder, parse_mode="Markdown")