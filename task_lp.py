from config import validate_config, setup_logging, STR_RPT_CHAT
from utils import get_now

setup_logging()
validate_config()

from gsheet_db_func import update_attendance_pm
from telegrambot import send_paradestate, send_reminder

today = get_now()
update_attendance_pm(today)
send_paradestate(STR_RPT_CHAT)
send_reminder(STR_RPT_CHAT)