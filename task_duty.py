from config import validate_config, setup_logging

setup_logging()
validate_config()

import gsheet_db_func

gsheet_db_func.update_db_from_gsheet_duty()
gsheet_db_func.update_db_from_gsheet_trooper_duty()