from datetime import datetime, timedelta
import pytz
import sqlite3
import os
import re
from thefuzz import process

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "alpha.db")

class NameConflict(Exception):
    pass

class DateError(Exception):
    pass

def get_today_col(worksheet, date):
    date = date.strftime("%d-%b-%y")
    cell = worksheet.find(date)
    A1col, A1row = split_A1(cell.address)
    col = cell.col
    return A1col, col

def split_A1(A1):
    col = ""
    row = ""
    for i in A1:
        if i.isalpha():
            col += i
        else:
            row += i
    return (col, row)

def convert_date_db_ymd(date):
    date = datetime.strptime(date, "%d-%b-%y")
    new_date = date.strftime("%y%m%d")
    return new_date

def convert_date_dmy_db(date):
    date = datetime.strptime(date, "%d%m%y")
    new_date = date.strftime("%d-%b-%y")
    return new_date

def convert_date_dmy_ymd(date):
    date = datetime.strptime(date, "%d%m%y")
    new_date = date.strftime("%y%m%d")
    return new_date

def convert_date_ymd_db(date):
    date = datetime.strptime(date, "%y%m%d")
    new_date = date.strftime("%d-%b-%y")
    return new_date

def convert_date_dmy_slash_ymd(date):
    try:
        date = datetime.strptime(date, "%d/%m/%y")
        new_date = date.strftime("%y%m%d")
        return new_date
    except:
        return date

def convert_date_dmy_dmy_slash(date):
    date = datetime.strptime(date, "%d%m%y")
    new_date = date.strftime("%d/%m/%y")
    return new_date

def convert_date_ymd_dmy_slash(date):
    try:
        date = datetime.strptime(date, "%y%m%d")
        new_date = date.strftime("%d/%m/%y")
        return new_date
    except:
        return date

def convert_date_ymd_dmy(date):
    try:
        date = datetime.strptime(date, "%y%m%d")
        new_date = date.strftime("%d%m%y")
        return new_date
    except:
        return date

def format_num_days(date_from, date_to):
    try:
        day = datetime.strptime(date_to,"%y%m%d") - datetime.strptime(date_from,"%y%m%d") + timedelta(days=1)
        result = "{}D".format(day.days)
        return result
    except:
        if date_from.upper() in "PERMANENT" or date_to.upper() in "PERMANENT":
            return "PERMANENT"
        else:
            return ""

def is4D(check):
    if len(check) == 4 and check.isdigit():
        return True
    else:
        return False

def get_now():
    tz = pytz.timezone("Asia/Singapore")
    return datetime.now(tz)

def get_name_index(target, lst):
    matches = process.extract(target,lst)
    best_match = matches[0] if matches else None
    if best_match:
        best_match_name, best_match_score = best_match
        repeated_highest_score = [i[0] for i in matches if i[1] == best_match_score]
        if len(repeated_highest_score) > 1:
            raise NameConflict(target, repeated_highest_score)
        elif best_match_score > 70:
            return lst.index(best_match_name)
    # index_lst = [i for i, item in enumerate(lst) if target in item]
    # return index_lst[0]

def get_index(target, lst):
    index_lst = [i for i, item in enumerate(lst) if target in item]
    return index_lst[0]

def is_date(msg):
    if len(msg) == 13 and len([i for i in msg.split("-") if i.isdigit()]) == 2:
        return True
    elif len(msg) == 6 and msg.isdigit():
        return True
    elif len(msg) > 0 and msg[-1].strip().upper() == "D" and msg[:-1].strip().isdigit():
        return True
    elif len(msg) > 0 and msg.upper() in "PERMANENT":
        return True
    else:
        return False

def parse_date(date):
    if len(date) > 0 and date[-1].strip().upper() == "D":
        tz = pytz.timezone("Asia/Singapore")
        today = datetime.now(tz)
        days = int(date[:-1].strip())
        if days == 1:
            return today.strftime("%d%m%y")
        else:
            date_from = today.strftime("%d%m%y")
            date_to = (today + timedelta(days=days-1)).strftime("%d%m%y")
            return "{}-{}".format(date_from,date_to)
    else:
        return date

def is_rank(check):
    ranks = ("REC", "PTE", "LCP", "CPL", "3SG", "2SG", "1SG", "SSG", "MSG", "3WO", "2WO", "1WO", "MWO", "2LT", "LTA", "CPT", "MAJ", "LTC", "COL")
    if check in ranks:
        return True
    return False

def is_incamp_notincamp(check):
    if check.strip().upper() in ("INCAMP", "NOTINCAMP", "IN CAMP", "NOT IN CAMP"):
        return True
    return False

def is_remarks(check):
    try:
        if "(" in check:
            return True
        return False
    except:
        return False
    
def is_end_remarks(check):
    try:
        if ")" in check:
            return True
        return False
    except:
        return False

def is_detail(check:str, table):
    if table == "ms":
        ms_check = ('MC', 'LD', 'RIB','EX')
        if check.strip().upper() in ms_check:
            return True
    elif table == "duty":
        duty_check = ('COS', 'DOS', 'GUARD DUTY', 'GD', 'COS DUTY', 'DOO', 'CDSO')
        if check.strip().upper() in duty_check:
            return True
    elif table == "others":
        others_check = ('DB', 'AWOL', 'COMP', 'COMPASSIONATE')
        if check.strip().upper() in others_check:
            return True
    return False

def check_others_incamp(msg_str):
    incamp = None
    if re.match(r'^.*incamp.*', msg_str, flags=re.IGNORECASE):
        msg_str = re.sub(r'^.*incamp.*', "", msg_str, flags=re.IGNORECASE)
        incamp = True
    elif re.match(r'^.*in camp.*', msg_str, flags=re.IGNORECASE):
        msg_str = re.sub(r'^.*in camp.*', "", msg_str, flags=re.IGNORECASE)
        incamp = True
    elif re.match(r'^.*notincamp.*', msg_str, flags=re.IGNORECASE):
        msg_str = re.sub(r'^.*notincamp.*', "", msg_str, flags=re.IGNORECASE)
        incamp = False
    elif re.match(r'^.*not incamp.*', msg_str, flags=re.IGNORECASE):
        msg_str = re.sub(r'^.*not incamp.*', "", msg_str, flags=re.IGNORECASE)
        incamp = False
    elif re.match(r'^.*not in camp.*', msg_str, flags=re.IGNORECASE):
        msg_str = re.sub(r'^.*not in camp.*', "", msg_str, flags=re.IGNORECASE)
        incamp = False
    return msg_str, incamp

def dict_lst_append(dict_lst:dict, key, item):
    if key in dict_lst.keys():
        dict_lst[key].append(item)
    else:
        dict_lst[key] = [item]

def dict_str_append(dict_lst:dict, key, item):
    if key in dict_lst.keys():
        dict_lst[key] += " {}".format(item)
    else:
        dict_lst[key] = item


def dict_get_item(dict_lst, key):
    try:
        return dict_lst[key]
    except:
        return ""

def eval_type(item, table):
    if is_date(item):
        return "DATE"
    elif is_detail(item, table):
        return "DETAILS"
    elif is_remarks(item):
        return "REMARKS"
    elif is_end_remarks(item):
        return "END REMARKS"
    elif is_rank(item):
        return "RANK"
    elif item.upper().strip() in ("STAYIN", "STAYOUT"):
        return "STAYOUT"
    else:
        return None

def check_name_detail_append(chain_str, data_dict, currently_name):
    if currently_name:
        dict_str_append(data_dict, "NAME", chain_str)
    else:
        dict_str_append(data_dict, "DETAILS", chain_str)

def parse_preffix(msg_str, data_dict):
    msg_lst = msg_str.split(" ")
    try:
        preffix = msg_lst[0].strip().upper()
        if preffix == "DELETE":
            data_dict["DELETE"] = True
            msg_str = " ".join(msg_lst[1:])
        else:
            data_dict["DELETE"] = False
        if preffix == "OOC":
            data_dict["OOC"] = True
            msg_str = " ".join(msg_lst[1:])
        else:
            data_dict["OOC"] = False
        return msg_str, data_dict
    except:
        return msg_str, data_dict
    
def count_non_empty(lst):
    return len([i for i in lst if i != ""])

def parse_start_remarks(curr_item, data_dict, table, currently_name, currently_remarks):
    item_lst = curr_item.split("(")
    if count_non_empty(item_lst) == 1:
        check_item = item_lst[0].strip() # set check item
    else: # multiple open brackets, error in input
        for i in item_lst[:1]:
            if i == "":
                continue
            bozo_input = i.replace(")", "").strip()
            if is_date(bozo_input):
                dict_lst_append(data_dict, "DATE", bozo_input)
            else:
                parse_data_item(bozo_input, eval_type(bozo_input, table), data_dict, currently_remarks, table, currently_name)
        check_item = item_lst[1].strip() # set check item
    if is_end_remarks(check_item): 
        currently_remarks = False
    else:
        currently_remarks = True
    remark = check_item.replace(")", "").strip()
    if is_date(remark):
        dict_lst_append(data_dict, "DATE", remark)
    else:
        dict_str_append(data_dict, "REMARKS", remark)
    return currently_remarks

def parse_end_remarks(curr_item, data_dict, table, currently_name, currently_remarks):
    item_lst = curr_item.split(")")
    check_item = item_lst[0].strip() # set check item
    dict_str_append(data_dict, "REMARKS", check_item)
    if count_non_empty(item_lst) > 1:
        for i in item_lst[1:]:
            if i == "":
                continue
            bozo_input = i.strip()
            parse_data_item(bozo_input, eval_type(bozo_input, table), data_dict, currently_remarks, table, currently_name)


def parse_data_item(item, item_type, data_dict, currently_remarks, table, currently_name):
    if item_type == None and currently_remarks == False:
        # unknown string, likely detail or name
        # if name is not inputed yet, goes to name, if name is inputted, goes to detail
        check_name_detail_append(item, data_dict, currently_name)
    elif item_type == None and currently_remarks == True:
        dict_str_append(data_dict, "REMARKS", item)
    elif item_type == "DATE":
        currently_name = False
        dict_lst_append(data_dict, "DATE", item)
    elif item_type == "REMARKS":
        currently_name = False
        currently_remarks = parse_start_remarks(item, data_dict, table, currently_name, currently_remarks)
    elif item_type == "END REMARKS":
        currently_name = False
        currently_remarks = parse_end_remarks(item, data_dict, table, currently_name, currently_remarks)
    else:
        currently_name = False
        dict_str_append(data_dict, item_type, item)
    return currently_remarks, currently_name

def parse_data(msg_str, data_dict, table):
    if table == "others":
        msg_str, incamp = check_others_incamp(msg_str)
        data_dict["InCamp"] = incamp
    msg_lst = [i for i in msg_str.split(" ") if i != ""]
    # check curr, check next, (no next just cut)
    # case: next != curr (new type): append 
    # case: next == curr (same type): append to temp var
    # None type -> likely to be name or detail, if no name yet, None type likely to be Name
    # if name already exist, None type likely to be detail
    i = 0
    currently_remarks = False
    currently_name = True
    while i < len(msg_lst):
        curr_item  = msg_lst[i]
        curr_type = eval_type(curr_item, table)
        currently_remarks, currently_name = parse_data_item(curr_item, curr_type, data_dict, currently_remarks, table, currently_name)
        i += 1
    return data_dict

def check_date_format(date):
    if len(date) == 13 and len([i for i in date.split("-") if i.isdigit()]) == 2:
        return "ddmmyy"
    elif len(date) == 6 and date.isdigit():
        return "ddmmyy"
    elif len(date) > 0 and date[-1].strip().upper() == "D" and date[:-1].strip().isdigit():
        return "D"
    else:
        return "perm"

def flatten_date(date_lst, data_dict):
    if len(date_lst) > 1:
        # if there are multiple dates inputed, check if all refers to the same date, just in different format
        days = [calc_num_days(i) for i in date_lst]
        if len(set(days)) == 1:
            # if all is same dates, just different format
            for date in date_lst:
                # prioritise specific dates
                if check_date_format(date) == "ddmmyy":
                    return date
                else:
                    result_date = date
            # if no specific dates, assume that D starts from today
            data_dict["D"] = True
            return parse_date(result_date)
        else:
            raise DateError
    elif len(date_lst) > 0:
        if check_date_format(date_lst[0]) == "ddmmyy":
            return date_lst[0]
        else:
            data_dict["D"] = True
            return parse_date(date_lst[0])
    else:
        return ""
    
def dict_fill(row_dict):
    dict_items = ("NAME", "RANK", "DATE", "DETAILS", "REMARKS", "DELETE", "D", "OOC", "STAYOUT", "InCamp", "4D")
    for item in dict_items:
        try:
            check = row_dict[item]
        except:
            row_dict[item] = ""

def flatten_data_dict(data_dict:dict):
    dict_lst = []
    for i in sorted(data_dict.keys()):
        # for each row if there is a name (row is valid/for input), all data in dict register under the row
        if dict_get_item(data_dict[i], "NAME"):
            row_dict = data_dict[i]
            dict_fill(row_dict)
            data_dict[i]["DATE"] = flatten_date(data_dict[i]["DATE"], data_dict[i])
            data_dict[i]["REMARKS"] = data_dict[i]["REMARKS"].strip()
            dict_lst.append(row_dict)
        else:
            # if there is no name (some bozo fked it up and put date in next line or wtv)
            # push the data up to the 
            for k in data_dict[i].keys():
                if k == "DATE":
                    data_dict[i][k] = flatten_date(data_dict[i][k], data_dict[i])
                curr_items = dict_get_item(data_dict[i], k)
                if curr_items == "" or curr_items == None:
                    continue
                for j in range(i-1, -1, -1):
                    prev_items = dict_get_item(data_dict[j], k)
                    if prev_items == None or prev_items == "":
                        dict_str_append(data_dict[j], k, curr_items)
                        break
    
    return dict_lst

def unformat_msg(msg_lst, table):
    # Rank, Name, Details, Date, Remarks
    data_dict = {}
    for i in range(len(msg_lst)):
        msg = msg_lst[i]
        msg, data_dict[i] = parse_preffix(msg, {})
        data_dict[i] = parse_data(msg, data_dict[i], table)
    dict_lst = flatten_data_dict(data_dict)
    return dict_lst


def date_error(date):
    date_list = date.split("-")
    today = datetime.now()
    for date in date_list:
        try:
            date_time = datetime.strptime(date, "%d%m%y")
        except:
            return "Date Format Error"
        if abs((date_time - today).days) > 90:
            return "Date Too Far"


def detect_error(msg_dict):
    if "InCamp" in msg_dict.keys() and msg_dict["InCamp"] == None:
        return "InCamp/NotInCamp not provided"
    elif msg_dict["NAME"] != "" and msg_dict["4D"] != "":
        return "If 4D is provided dont need name, Details shld be after Date"
    elif date_error(msg_dict["DATE"]):
        return date_error(msg_dict["DATE"])
    elif msg_dict["DETAILS"] == "":
        return "No Details Provided"


def reformat_mass_msg(msg_lst):
    # func takes in a list: msg.split("\n")
    """
    MSG FORMAT:
    Date Details
    RANK NAME
    E.G.:
    050124 Guard Duty
    3SG JOHN
    3SG JACK RESERVE
    """
    reformated_msg = []
    header = {"DATE":"","DETAILS":[]}
    for msg_line in msg_lst:
        msg_line = msg_line.strip().split(" ")
        # print(msg_line)
        # if the line is a header
        if is_date(msg_line[0]):
            header["DATE"] = parse_date(msg_line.pop(0))
            header["DETAILS"] = " ".join(msg_line)
            # print(header)
        # else if the line is a data
        elif len(msg_line) > 0:
            msg_line.append(header["DATE"])
            msg_line.append(header["DETAILS"])
            reformated_msg.append(" ".join(msg_line))
    return reformated_msg

def get_stayout():
    db = sqlite3.connect(db_path)
    query = "SELECT Rank, Name FROM SoldierInfo WHERE StayOut = 'True'"
    cursor = db.execute(query)
    data = cursor.fetchall()
    output = ""
    for row in data:
        output += "{} {}\n".format(row[0], row[1])
    db.close()
    return output.strip()

def filter_mc_data(data):
    if data and len(data) > 0:
        result = [data.pop(0)]
        for row in data:
            if row[1] == result[-1][1] and row[4] > result[-1][4]:
                result.pop()
                result.append(row)
            else:
                result.append(row)
        return result
    else:
        return data

def calc_num_days(date):
    if date[-1] == "D":
        try:
            return int(date[:-1])
        except:
            return ""
    else:
        try:
            date_from_to = date.split("-")
            if len(date_from_to) == 2:
                date_from, date_to = date_from_to
            else:
                date_from, date_to = date_from_to[0], date_from_to[0]
            day = datetime.strptime(date_to,"%d%m%y") - datetime.strptime(date_from,"%d%m%y") + timedelta(days=1)
            return day.days
        except:
            if date_from.upper() in "PERMANENT" or date_to.upper() in "PERMANENT":
                return "PERMANENT"
            else:
                return ""

def format_num_days_slash(date_from, date_to):
    try:
        day = datetime.strptime(date_to,"%d/%m/%y") - datetime.strptime(date_from,"%d/%m/%y") + timedelta(days=1)
        result = "{}D".format(day.days)
        return result
    except:
        if date_from.upper() in "PERMANENT" or date_to.upper() in "PERMANENT":
            return "PERMANENT"
        else:
            return ""

def unlock_db():
    db = sqlite3.connect(db_path)
    query = """SELECT * FROM GroupSettings"""
    cursor = db.execute(query)
    data = cursor.fetchall()
    db.commit()
    db.close()

def generate_soldierID(header, name, current_soldierID_list):
    '''
    ID FORMAT: {Battalion}{Mono}{Coy}-{1st5ChrOfName}{RepeatedIDIncrement}
    E.G. 3SIR19A-ZHOUZE01
    '''
    soldier_ID = "{header}-{name}{incre}"
    formatted_name = re.sub(r'[^\w]', '', name.upper())[:6]
    increment = [i for i in current_soldierID_list if formatted_name in i]
    count = len(increment) + 1
    return soldier_ID.format(header=header,name=formatted_name,incre=f'{count:02}')

print(unformat_msg(["PARRIS 2D MC (FEVER & DIARRHOEA)"], "ms"))