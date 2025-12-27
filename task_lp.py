from gsheet_db_func import update_attendance_pm
from telegrambot import send_paradestate, send_reminder
from utils import get_now

today = get_now()
update_attendance_pm(today)
send_paradestate("ALPHA STR RPT")
send_reminder("ALPHA STR RPT")