# Admin Bot

A Telegram bot for tracking company attendance and statuses. It keeps a SQLite
database in sync with Google Sheets and generates parade states, book-in/book-out
strength reports, and status histories on demand.

Originally built for one company, now configurable so any unit can run it.

## What you need

- Python 3.11+
- A Telegram bot token (from [@BotFather](https://t.me/BotFather))
- A Google Cloud service account with the Sheets API enabled
- Three Google Sheets (or one, if you keep everything in a single spreadsheet):
  paradestate, commander duty, trooper duty

## Setup

1. Install dependencies:

   ```
   python -m venv .venv
   .venv/Scripts/activate          # Windows
   source .venv/bin/activate       # Linux/Mac
   pip install -r requirements.txt
   ```

2. Get Google credentials:
   - In the [Google Cloud Console](https://console.cloud.google.com/), create a
     project, enable the **Google Sheets API** and **Google Drive API**, and
     create a **service account**. Download its JSON key as `service_account.json`
     in the project root.
   - Share each spreadsheet with the service account's email (found in the JSON).

3. Configure:

   ```
   cp .env.example .env
   ```

   Then fill in `.env` with your bot token, chat ids, sheet urls and service
   account path. See the comments in `.env.example` for each value.

4. Create the database:

   ```
   python init_db.py --seed-groups
   ```

   Edit `seed_groups.sql` first if your unit's platoon/section structure differs
   from the example.

5. (Optional) Generate fresh Google Sheets templates:

   ```
   python init_sheets.py --share you@gmail.com
   ```

   This creates the three spreadsheets with the right headers and prints their
   urls to paste into `.env`.

6. Run the bot:

   ```
   python main.py
   ```

## Scheduled tasks

These are meant to be run on a schedule (cron, Task Scheduler, etc):

| Script           | When                | What it does                                   |
|------------------|---------------------|------------------------------------------------|
| `task_duty.py`   | start of each day   | pull duties from the duty sheets into the db   |
| `task_fp.py`     | first parade        | update AM attendance, send parade state        |
| `task_lp.py`     | last parade         | update PM attendance, send parade state        |
| `task_dailys.py` | a few times a day   | send movement-day reminders                    |

## Configuration

Everything sensitive or unit-specific lives in `.env` (never committed). Key
values:

- `BOT_TOKEN` — Telegram bot token
- `CHAT_CONFIG` — JSON mapping chat names to chat/topic ids
- `GOOGLE_SERVICE_ACCOUNT_FILE` — path to the credentials JSON
- `PARADESTATE_SHEET_URL`, `COMMANDER_DUTY_SHEET_URL`, `TROOPER_DUTY_SHEET_URL`
- `UNIT_ID_HEADER` — prefix for generated soldier ids (e.g. `3SIR19A`)
- `DB_PATH` — SQLite file location


## How it fits together

- **task_telebot.py** — Telegram command and message handlers. Commands generate
  parade states / strength reports; messages with a header (`STATUS:`, `DUTY:`,
  `LEAVE:`, `MA:`, `COURSE:`, `OTHERS:`, `RSI:`, `RSO:`, `ORD`) update records.
- **gsheet_db_func.py** — the backend between the bot, the database, and the
  sheets. Attendance updates, sheet/db sync, and all the record writers live here.
  Most logic bugs, if any, will be in the attendance functions.
- **paradestate_func.py** — builds parade state messages from the database only.
- **book_in_str.py** — builds book-in/book-out strength. Absentees come from
  `get_absent()`.
- **utils.py** — date conversions, message parsing, fuzzy name matching, id
  generation.
- **config.py** — settings (from `.env`) and message format templates.
- **excel_through_basics.py** — recruit attendance and ration helpers.

### Updating attendance (gsheet_db_func)

- Attendance is updated in the database before a parade state is generated, using
  data from the sheet.
- AM and PM differ: last parade excludes stay-outs, and on book-out days everyone
  is absent except those on duty.

### Updating soldier info

- `update_db_info_from_gsheet` adds/updates/removes soldiers based on the sheet.
  A new id is generated from the name with an increment for duplicates.
- **Removing a soldier deletes their records.** Back up first.

### Updating duties / leave

- Duties are pulled daily from the commander and trooper duty sheets. The format
  matters — dates, rows and columns are read by position, so update the code if
  your sheet layout changes.
- Leave is read a few days in advance from the commander sheet.

## Adding days to the sheet

`add_days_gsheet` (via the `/add_days` command) appends date columns to the
paradestate sheet. Archive old sheets periodically to keep things fast.
