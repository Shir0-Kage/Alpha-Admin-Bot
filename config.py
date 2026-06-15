import json
import logging
import os

from dotenv import load_dotenv

# read .env if it's there, real env vars still win
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _env(name, default=""):
    value = os.getenv(name, default)
    return value.strip() if isinstance(value, str) else value


# Telegram
BOT_TOKEN = _env("BOT_TOKEN")

# friendly chat name -> {"CHAT_ID": ..., "THREAD_ID": ...}, passed in as JSON
try:
    CHAT_ID = json.loads(_env("CHAT_CONFIG", "{}") or "{}")
except json.JSONDecodeError as exc:
    raise ValueError('CHAT_CONFIG must be valid JSON, e.g. {"STR RPT": {"CHAT_ID": -100123, "THREAD_ID": 5}}') from exc

# which CHAT_CONFIG keys the daily tasks send to
STR_RPT_CHAT = _env("STR_RPT_CHAT", "STR RPT")
BOT_UPDATES_CHAT = _env("BOT_UPDATES_CHAT", "BOT UPDATES")

# Google Sheets
GOOGLE_SERVICE_ACCOUNT_FILE = _env("GOOGLE_SERVICE_ACCOUNT_FILE", os.path.join(BASE_DIR, "service_account.json"))

# the three spreadsheets we read/write. set all three to the same url if you keep everything in one.
PARADESTATE_SHEET_URL = _env("PARADESTATE_SHEET_URL")
COMMANDER_DUTY_SHEET_URL = _env("COMMANDER_DUTY_SHEET_URL")
TROOPER_DUTY_SHEET_URL = _env("TROOPER_DUTY_SHEET_URL")

# old code used a single sheet_url, keep it pointing at the paradestate sheet
sheet_url = PARADESTATE_SHEET_URL

# prefix for generated soldier ids, e.g. 3SIR19A -> 3SIR19A-ZHOUZE01
UNIT_ID_HEADER = _env("UNIT_ID_HEADER", "UNIT")

DB_PATH = _env("DB_PATH", os.path.join(BASE_DIR, "alpha.db"))

LOG_LEVEL = _env("LOG_LEVEL", "INFO").upper()


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


_gspread_client = None


def get_gspread_client():
    # built on first use so importing config doesn't need credentials
    global _gspread_client
    if _gspread_client is None:
        import gspread

        if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(
                f"service account file not found at '{GOOGLE_SERVICE_ACCOUNT_FILE}', "
                "set GOOGLE_SERVICE_ACCOUNT_FILE in your .env"
            )
        _gspread_client = gspread.service_account(GOOGLE_SERVICE_ACCOUNT_FILE)
    return _gspread_client


class _ServiceAccountProxy:
    # SERVICE_ACCOUNT used to be a ready gspread client; now it's resolved on first use
    def __getattr__(self, item):
        return getattr(get_gspread_client(), item)

    def __call__(self, *args, **kwargs):
        return get_gspread_client()


SERVICE_ACCOUNT = _ServiceAccountProxy()


def validate_config():
    # call this from the entry points so we stop early with a clear message
    missing = []
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not PARADESTATE_SHEET_URL:
        missing.append("PARADESTATE_SHEET_URL")
    if not COMMANDER_DUTY_SHEET_URL:
        missing.append("COMMANDER_DUTY_SHEET_URL")
    if not TROOPER_DUTY_SHEET_URL:
        missing.append("TROOPER_DUTY_SHEET_URL")
    if missing:
        raise RuntimeError("Missing config: " + ", ".join(missing) + ". Copy .env.example to .env and fill it in.")
    if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"service account file not found at '{GOOGLE_SERVICE_ACCOUNT_FILE}'")


PARADESTATE_FORMAT = """
A COY PARADE STRENGTH CAA {date} {time}HRS


Total Commander: {totalcommanderstr}
Total Support Staff: -/0


Grand Total: {grandtotal}
Total Officer: {totalofficer}
Total WOSE: {totalwose}


Personnel on DB/AWOL/CC/CA: 00
------------------------------------------

COY HQ
TOTAL STRENGTH: {coyhqstr}
OFFICER: {coyhqofficerstr}
{coyhqofficers}

WOSE: {coyhqwosestr}
{coyhqwose}

Commander: {coyhqstr}
Support Staff: -/0

----------------------------------------------

PLT HQ
TOTAL STRENGTH: {plthqstr}
OFFICER: -/0

WOSE: {plthqwosestr}
{plthqwose}

Commander: {plthqstr}
Support Staff: -/0

----------------------------------------------

❌ STATUS: {statusstr}
{status}

😷MC: {mcstr}
{mc}

👨🏻⚕MA: {mastr}
{ma}

🚪LEAVE: {leavestr}
{leave}

🏠STAY OUT: {stayoutstr}
{stayout}

🎓ON COURSE: {oncoursestr}
{oncourse}

🚨ON DUTY: {dutystr}
{duty}

📔OTHERS: {otherstr}
{others}
"""

HEADER_FORMAT = """
A COY PARADE STRENGTH CAA {date} {time}HRS

Total Commander: {total_commander_str}
Total Support Staff: {total_support_staff_str}
Total Troopers: {total_trooper_str}

Grand Total: {grand_total}
Total Officer: {total_officer}
Total WOSE: {total_wose}

Personnel on DB/AWOL/CC/CA: {dbAwolCcCA}
"""

DIVIDER = "-----------------------------------"

GROUP_FORMAT = """
{group_name}
TOTAL STRENGTH: {total_str}
OFFICER: {officer_str}
{officers}
WOSE: {wose_str}
{wose}
Commander: {commander_str}
"""

SUPPORT_STAFF_FORMAT = "Support Staff: {}"

TROOPER_FORMAT = "Trooper: {}"

SPECIAL_CASE_FORMAT = """
❌ STATUS: {status_str}
{status}

😷MC: {mc_str}
{mc}

👨🏻⚕MA: {ma_str}
{ma}

🚪LEAVE: {leave_str}
{leave}

🏠STAY OUT: {stayout_str}
{stayout}

🎓ON COURSE: {oncourse_str}
{oncourse}

🚨ON DUTY: {duty_str}
{duty}

📔OTHERS: {others_str}
{others}"""


RECRUIT_HEADER_FORMAT = """
{group} PARADESTATE {date} {time} HRS

Recruits Grand Total: {grand_total}
"""

COMMANDERS_GROUP_FORMAT = """
Commanders
---------------------
Total Commanders: {total_str}

Absent: {absent_strength}
{absent_nr}
"""

RECRUIT_GROUP_FORMAT = """
Total {group_name}: {group_strength}
Total S1: {s1_str}
Total S2: {s2_str}
Total S3: {s3_str}
Total S4: {s4_str}

MC: {mc_count}
{mc_nr}
RIB: {rib_count}
{rib_nr}
Status: {status_count}
{status_nr}
Status Day 1: {status_d1_count}
{status_d1_nr}
RSI: {rsi_count}
{rsi_nr}
RSO: {rso_count}
{rso_nr}
Others: {others_count}
{others_nr}
"""

BOOK_IN_STR_HEADER = """*Alpha Coy Book {in_or_out} Strength caa {date} {time}*

*Total strength: {total_coy}*
- *Commander: {total_comd}*
- *Trooper strength: {total_trooper}*
- *Support staff: {total_staff}*

"""

BOOK_IN_STR_GROUP = """*{group_name}*
{group_tag} Strength: {total_group}
-Comd: {total_comd}
{comd_absent}"""


BOOK_IN_STR_GROUP_STAFF = """-Staff: {total_staff}
{staff_absent}
"""

# removed status
BOOK_IN_STR_GROUP_TROOPER = """-Troopers: {total_trooper}
{absent}
"""

TRIPLINE_MSG = """*Alpha Coy Triplines caa {date}*
Total Monitoring: {total_monitoring} pax
Tripline 2: {tripline2_count} pax
Tripline 3: {tripline3_count} pax

*Tripline 2 - 4 to 7 Days*
{tripline2_nr}

*Tripline 3 - 8 to 11 Days*
{tripline3_nr}

 *Special absentees cases/ Problematic Personnel*
{special_case}

*Key Updates/ Actionables*
1. """
