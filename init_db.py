"""Set up the sqlite database.

    python init_db.py                 create the tables
    python init_db.py --seed-groups   also seed GroupSettings if empty
    python init_db.py --db other.db   use a different db file

Defaults to config.DB_PATH. Re-running won't wipe existing data.
"""

import argparse
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILE = os.path.join(BASE_DIR, "schema.sql")
SEED_GROUPS_FILE = os.path.join(BASE_DIR, "seed_groups.sql")


def _default_db_path():
    try:
        from config import DB_PATH

        return DB_PATH
    except Exception:
        return os.path.join(BASE_DIR, "alpha.db")


def init_db(db_path, seed_groups=False):
    with open(SCHEMA_FILE, "r", encoding="utf-8") as fh:
        schema_sql = fh.read()

    db = sqlite3.connect(db_path)
    try:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript(schema_sql)
        db.commit()
        print(f"Schema applied to '{db_path}'.")

        if seed_groups:
            count = db.execute("SELECT COUNT(*) FROM GroupSettings").fetchone()[0]
            if count == 0:
                with open(SEED_GROUPS_FILE, "r", encoding="utf-8") as fh:
                    db.executescript(fh.read())
                db.commit()
                seeded = db.execute("SELECT COUNT(*) FROM GroupSettings").fetchone()[0]
                print(f"Seeded GroupSettings with {seeded} rows.")
            else:
                print(f"GroupSettings already has {count} rows, skipping seed.")
    finally:
        db.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Set up the bot database.")
    parser.add_argument("--db", default=_default_db_path(), help="db file (default: config.DB_PATH)")
    parser.add_argument("--seed-groups", action="store_true", help="seed GroupSettings if empty")
    args = parser.parse_args(argv)

    init_db(args.db, seed_groups=args.seed_groups)
    return 0


if __name__ == "__main__":
    sys.exit(main())
