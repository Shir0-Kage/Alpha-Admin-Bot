"""Create starter Google Sheets for a new deployment.

Makes the three spreadsheets the bot expects (paradestate, commander duty,
trooper duty) with the right header rows, then prints the urls to drop into
your .env. Needs GOOGLE_SERVICE_ACCOUNT_FILE set up first.

    python init_sheets.py
    python init_sheets.py --share you@gmail.com   also share them with you
    python init_sheets.py --days 30               number of date columns

The layouts match what the bot reads, but you can rearrange them later as long
as the key rows/columns stay put (see comments below).
"""

import argparse
import sys
from datetime import timedelta

from gspread.utils import rowcol_to_a1

import config
import utils


def _range(r1, c1, r2, c2):
    return "{}:{}".format(rowcol_to_a1(r1, c1), rowcol_to_a1(r2, c2))


# paradestate sheet, first worksheet:
#   row 1 = day of week (above each date column)
#   row 2 = info headers in cols 1-9, then dates (dd-Mon-yy) from col 10 on
#   row 3 = the day's activity (MOVEMENT / WEEKEND / ...)
#   row 4+ = one soldier per row
INFO_HEADERS = ["No.", "SoldierID", "Rank", "Name", "PLT", "SCT", "GRP", "StayOut", "Ration"]
FIRST_DATE_COL = len(INFO_HEADERS) + 1  # column J


def _date_columns(start, days):
    rows = {1: [], 2: [], 3: []}
    d = start
    for _ in range(days):
        day = d.strftime("%a").upper()
        rows[1].append(day)
        rows[2].append(d.strftime("%d-%b-%y"))
        rows[3].append("WEEKEND" if day in ("SAT", "SUN") else "MOVEMENT")
        d += timedelta(days=1)
    return rows


def build_paradestate(gc, days, share_email):
    sh = gc.create("Paradestate")
    ws = sh.get_worksheet(0)
    ws.update_title("Paradestate")

    cells = _date_columns(utils.get_now(), days)
    requests = [
        {"range": "A2:I2", "values": [INFO_HEADERS]},
        {"range": _range(1, FIRST_DATE_COL, 1, FIRST_DATE_COL + days - 1), "values": [cells[1]]},
        {"range": _range(2, FIRST_DATE_COL, 2, FIRST_DATE_COL + days - 1), "values": [cells[2]]},
        {"range": _range(3, FIRST_DATE_COL, 3, FIRST_DATE_COL + days - 1), "values": [cells[3]]},
    ]
    ws.batch_update(requests)
    _share(sh, share_email)
    return sh


def build_commander_duty(gc, days, share_email):
    sh = gc.create("Commander Duty")
    ws = sh.get_worksheet(0)
    # row 1 = dates (dd/mm/yy) from col 3, names down col 2 from row 2
    dates = [(utils.get_now() + timedelta(days=i)).strftime("%d/%m/%y") for i in range(days)]
    header = ["", "Name"] + dates
    ws.update([header], "A1")
    _share(sh, share_email)
    return sh


def build_trooper_duty(gc, share_email):
    sh = gc.create("Trooper Duty")
    ws = sh.get_worksheet(0)
    # bot looks for a worksheet named like "Jun 25" with: col1 date, col4 name, col5 unit
    ws.update_title(utils.get_now().strftime("%b %y").capitalize())
    ws.update([["Date", "Day", "Duty", "Name", "Unit"]], "A1")
    _share(sh, share_email)
    return sh


def _share(spreadsheet, email):
    if email:
        spreadsheet.share(email, perm_type="user", role="writer")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create starter Google Sheets.")
    parser.add_argument("--share", help="email to share the new sheets with")
    parser.add_argument("--days", type=int, default=30, help="how many date columns to add")
    args = parser.parse_args(argv)

    gc = config.get_gspread_client()

    para = build_paradestate(gc, args.days, args.share)
    comd = build_commander_duty(gc, args.days, args.share)
    troop = build_trooper_duty(gc, args.share)

    print("\nDone. Put these into your .env:\n")
    print(f"PARADESTATE_SHEET_URL={para.url}")
    print(f"COMMANDER_DUTY_SHEET_URL={comd.url}")
    print(f"TROOPER_DUTY_SHEET_URL={troop.url}")
    if not args.share:
        print("\n(Tip: pass --share you@gmail.com to open them in your own Drive.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
