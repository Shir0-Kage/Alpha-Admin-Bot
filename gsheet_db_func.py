from datetime import datetime, timedelta
import sqlite3
import os
from gspread.cell import Cell
from gspread.utils import rowcol_to_a1
from config import SERVICE_ACCOUNT, sheet_url
import utils
import pytz

class NotFound(Exception):
    pass

class NoDetail(Exception):
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "alpha.db")


def update_stayout_am():
    db = sqlite3.connect(db_path)
    query = "UPDATE SoldierInfo SET StayOut = 'False'"
    db.execute(query)
    db.commit()
    db.close()

def update_permanent(worksheet,date_param):
    today = utils.get_now()
    if date_param.strftime("%d%m%y") != today.strftime("%d%m%y"):
        return
    else:
        db = sqlite3.connect(db_path)

        soldierid_col = 2
        soldierid_list = worksheet.col_values(soldierid_col)

        query = "SELECT SoldierID From Others WHERE CASE WHEN DateTo = 'PERMANENT' OR DateTo = '' THEN 1 ELSE 0 END AND InCamp = 'False'"
        cursor = db.execute(query)
        data = cursor.fetchall()

        to_update = []

        A1col, today_col = utils.get_today_col(worksheet,date_param)

        for row in data:
            soldier_row = utils.get_index(row[0], soldierid_list) + 1
            to_update.append(Cell(row=soldier_row,col=today_col,value="Others"))
        db.close()
        if len(to_update) > 0:
            worksheet.update_cells(to_update)


def update_stayout_pm(worksheet):
    db = sqlite3.connect(db_path)
    today = utils.get_now()
    date = today.strftime("%y%m%d")
    soldierid_col = 2
    stayout_col = 8
    soldierid_list = worksheet.col_values(soldierid_col)
    stayout_list = worksheet.col_values(stayout_col)

    get_query = "SELECT InCamp From Attendance WHERE SoldierID = ?"
    get_ex_stayin_query = """SELECT SoldierInfo.SoldierID, MedicalStatus
                             FROM SoldierInfo, MedicalStatus
                             WHERE SoldierInfo.SoldierID = MedicalStatus.SoldierID
                             AND ? <= MedicalStatus.DateTo"""
    update_query = "UPDATE SoldierInfo SET StayOut = ? WHERE SoldierID = ?"
    update_attendance_query = "UPDATE Attendance SET InCamp = ? WHERE SoldierID = ?"

    status_data = db.execute(get_ex_stayin_query, (date,)).fetchall()
    ex_stayin_data = [i[0] for i in status_data if "ex" in i[1].lower() and "stay" in i[1].lower() and "in" in i[1].lower()]

    for i, stayout in enumerate(stayout_list):
        soldierid = soldierid_list[i]
        if stayout == "Yes" or soldierid in ex_stayin_data:
            cursor = db.execute(get_query, (soldierid,))
            data = cursor.fetchone()
            if data and data[0] == "True":
                db.execute(update_query, ('True',soldierid))
                db.execute(update_attendance_query, ('False',soldierid))
            else:
                db.execute(update_query, ('False',soldierid))
    db.commit()
    db.close()

def update_rso(worksheet,date_param):
    today = utils.get_now()
    if date_param.strftime("%d%m%y") != today.strftime("%d%m%y"):
        return
    else:
        db = sqlite3.connect(db_path)
        soldier_id_list = worksheet.col_values(2)
        to_update = []

        query = """SELECT SoldierInfo.SoldierID FROM SoldierInfo, ReportingSick
        WHERE SoldierInfo.SoldierID = ReportingSick.SoldierID
        AND Location = 'RSO'"""
        data = db.execute(query).fetchall()
        A1col, today_col = utils.get_today_col(worksheet,date_param)

        for row in data:
            soldier_id = row[0]
            soldier_row = utils.get_index(soldier_id, soldier_id_list) + 1
            to_update.append(Cell(row=soldier_row,col=today_col,value="RSO"))
        if len(to_update) > 0:
            worksheet.update_cells(to_update)



#### FUNCTION: UPDATES DB ATTENDANCE TABLE FOR WHO IS IN CAMP FOR THE DAY ####
## TESTED: OK
def update_attendance_am(date):
    db = sqlite3.connect(db_path)
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.get_worksheet(0)
    update_stayout_am()
    update_permanent(worksheet,date)
    update_rso(worksheet,date)

    id_list = worksheet.col_values(2)
    A1col, col = utils.get_today_col(worksheet,date)

    records = worksheet.col_values(col)

    staying_in_camp = ("IN CAMP", "COS DUTY", "GUARD DUTY", "DOS", "DOO", "CDSO", "GD")
    query = '''
        UPDATE Attendance
        SET InCamp = ?
        WHERE SoldierID = ?
        '''
    to_update = []
    today_activity = records[2]
    for i in range(3,len(id_list)):
        soldierid = id_list[i]
        if today_activity == "MOVEMENT":
            # out of range == "" == no special cases
            if i > len(records)-1:
                to_update.append(Cell(row=i+1,col=col,value="In Camp"))
                db.execute(query, ("True", soldierid))
            elif records[i] == "":
                to_update.append(Cell(row=i+1,col=col,value="In Camp"))
                db.execute(query, ("True", soldierid))
            # if staying in camp: dont need to update sheets
            elif records[i].upper() in staying_in_camp:
                db.execute(query, ("True", soldierid))
            else:
                db.execute(query, ("False", soldierid))
        # if today is a weekend
        else:
            # weeekend out of range == "" no special cases == not in camp
            if i > len(records)-1:
                db.execute(query, ("False", soldierid))
            # if staying in camp: dont need to update sheets
            elif records[i].upper() in staying_in_camp:
                db.execute(query, ("True", soldierid))
            else:
                db.execute(query, ("False", soldierid))
    db.commit()
    db.close()
    if len(to_update) > 0:
        worksheet.update_cells(to_update)

# show full attendance even on weekends
def update_recruits_attendance_am(date):
    db = sqlite3.connect(db_path)
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.get_worksheet(0)
    update_stayout_am()
    update_permanent(worksheet,date)
    update_rso(worksheet,date)

    id_list = worksheet.col_values(2)
    A1col, col = utils.get_today_col(worksheet,date)

    records = worksheet.col_values(col)
    sct_list = worksheet.col_values(6)

    active = ("IN CAMP")
    query = '''
        UPDATE Attendance
        SET InCamp = ?
        WHERE SoldierID = ?
        '''
    for i in range(3,len(id_list)):
        soldierid = id_list[i]
        # out of range == "" == no special cases
        if i > len(records)-1:
            db.execute(query, ("True", soldierid))
        elif records[i] == "":
            db.execute(query, ("True", soldierid))
        # if staying in camp: dont need to update sheets
        elif records[i].upper() in active:
            db.execute(query, ("True", soldierid))
        else:
            db.execute(query, ("False", soldierid))
    db.commit()
    db.close()


#### FUNCTION: UPDATES DB ATTENDANCE TABLE FOR WHO IS STAYING IN CAMP OVERNIGHT ####
## TESTED: OK
def update_attendance_pm(date):
    db = sqlite3.connect(db_path)
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.get_worksheet(0)

    A1col, col = utils.get_today_col(worksheet,date)
    on_duty = ("COS DUTY", "GUARD DUTY", "DOS", "DOO", "CDSO", "GD")
    notincamp = ("RSO", "OTHERS", "MC")
    id_list = worksheet.col_values(2)
    today_list = worksheet.col_values(col)
    today_activity = today_list[2]
    tmr_list = worksheet.col_values(col+1)
    tmr_activity = tmr_list[2]
    query = '''
        UPDATE Attendance
        SET InCamp = ?
        WHERE SoldierID = ?
        '''
    for i in range(3, len(id_list)):
        soldierid = id_list[i]
        if tmr_activity == "MOVEMENT":
            # case where tomorrow has movement, but soldier is on MC today, so they book in tomorrow
            if i < len(today_list) and today_list[i].upper() in notincamp:
                db.execute(query, ("False", soldierid))
                continue
            # case where tomorrow has movement and soldier have no special cases
            elif i > len(tmr_list)-1:
                db.execute(query, ("True", soldierid))
            # case where soldier in on duty
            elif i < len(today_list) and today_list[i].upper() in on_duty:
                db.execute(query, ("True", soldierid))
            # case where tomorrow has movement and soldier have no special cases
            elif tmr_list[i].upper() in ("", "IN CAMP"):
                db.execute(query, ("True", soldierid))
            # case where tomorrow has movement, but soldier is on leave tomorrow
            elif tmr_list[i].upper() in ("OVERSEAS LEAVE", "LOCAL LEAVE", "MC", "OFF", "ON COURSE", "LEAVE"):
                db.execute(query, ("False", soldierid))
            # case where tomorrow has movement while today doesn't (sun)
            elif today_activity.upper() in ("BLOCK LEAVE", "WEEKEND", "PUBLIC HOLIDAY"):
                db.execute(query, ("True", soldierid))
            else:
                db.execute(query, ("False", soldierid))
        # tommorow has no movement
        else:
            # case where tomorrow has no movement (fri) but soldier stays in camp as they have duty today
            if i < len(today_list) and today_list[i].upper() in on_duty:
                db.execute(query, ("True", soldierid))
            # case where soldier bookout on fri
            elif i > len(tmr_list)-1:
                db.execute(query, ("False", soldierid))
            elif tmr_list[i] == "In Camp":
                db.execute(query, ("True", soldierid))
            else:
                db.execute(query, ("False", soldierid))
        db.commit()
    db.close()
    update_stayout_pm(worksheet)
    db.close()


# def update_recruits_attendance_pm(date):
#     db = sqlite3.connect(db_path)
#     gc = SERVICE_ACCOUNT
#     sh = gc.open_by_url(sheet_url)
#     worksheet = sh.get_worksheet(0)

#     A1col, col = utils.get_today_col(worksheet,date)
#     on_duty = ("COS Duty", "Guard Duty", "DOS", "DOO", "CDSO")
#     notincamp = ("MC", "RSO", "Others")
#     id_list = worksheet.col_values(2)
#     stayout_list = worksheet.col_values(8)
#     today_list = worksheet.col_values(col)
#     today_activity = today_list[2]
#     tmr_list = worksheet.col_values(col+1)
#     tmr_activity = tmr_list[2]
#     query = '''
#         UPDATE Attendance
#         SET InCamp = ?
#         WHERE SoldierID = ?
#         '''
#     for i in range(3, len(id_list)):
#         soldierid = id_list[i]
#         stayout = stayout_list[i]
#         if tmr_activity == "MOVEMENT":
#             # case where tomorrow has movement, but soldier is on MC today, so they book in tomorrow
#             if i < len(today_list) and today_list[i] in notincamp:
#                 db.execute(query, ("False", soldierid))
#             # case where tomorrow has movement and soldier have no special cases
#             elif i > len(tmr_list)-1:
#                 db.execute(query, ("True", soldierid))
#             # case where soldier in on duty
#             elif i < len(today_list) and today_list[i] in on_duty:
#                 db.execute(query, ("True", soldierid))
#             # case where tomorrow has movement and soldier have no special cases
#             elif tmr_list[i] in ("", "In Camp"):
#                 db.execute(query, ("True", soldierid))
#             # case where tomorrow has movement, but soldier is on leave tomorrow
#             elif tmr_list[i] in ("Overseas Leave", "Local Leave", "MC", "Off", "On Course"):
#                 db.execute(query, ("False", soldierid))
#             # case where tomorrow has movement while today doesn't (sun)
#             elif today_activity in ("BLOCK LEAVE", "WEEKEND", "PUBLIC HOLIDAY"):
#                 db.execute(query, ("True", soldierid))
#             else:
#                 db.execute(query, ("False", soldierid))
#         # tommorow has no movement
#         else:
#             # case where tomorrow has no movement (fri) but soldier stays in camp as they have duty today
#             if i < len(today_list) and today_list[i] in on_duty:
#                 db.execute(query, ("True", soldierid))
#             # case where soldier bookout on fri
#             elif i > len(tmr_list)-1:
#                 db.execute(query, ("False", soldierid))
#             elif tmr_list[i] == "In Camp":
#                 db.execute(query, ("True", soldierid))
#             else:
#                 db.execute(query, ("False", soldierid))
#         db.commit()
#     update_stayout_pm(worksheet)
#     db.close()


#### FUNCTION: UPDATE SOLDIDER INFO DB ACCORDING TO GOOGLESHEET ####
## TESTED: WORKING
def update_db_info_from_gsheet():
    today = utils.get_now().strftime("%y%m%d")
    db = sqlite3.connect(db_path)
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    records = worksheet.get_all_values()[3:]

    id_list = worksheet.col_values(2)
    query = "SELECT SoldierID FROM SoldierInfo"
    cursor = db.execute(query)
    db_id_list = [i[0] for i in cursor.fetchall()]

    for db_id in db_id_list:
        if db_id not in id_list:
            delete_db_info(db_id, today)
    db.commit()
    db.close()
    to_update = []
    for i, soldier_record in enumerate(records):
        # To update when new soldierID is added
        soldier_info = soldier_record[:8]
        new_soldierID = update_db_info(soldier_info,id_list)
        if new_soldierID:
            to_update.append(Cell(col=2,row=i+4,value=new_soldierID))
    if len(to_update) > 0:
        worksheet.update_cells(to_update)

def delete_db_info(soldier_id, date):
    db = sqlite3.connect(db_path)

    delete_status = "DELETE FROM MedicalStatus WHERE SoldierID = ? AND DateTo >= ?"
    db.execute(delete_status, (soldier_id,date))
    delete_ma = "DELETE FROM MedicalAppointment WHERE SoldierID = ? AND Date >= ?"
    db.execute(delete_ma, (soldier_id,date))
    delete_others = "DELETE FROM Others WHERE SoldierID = ?"
    db.execute(delete_others, (soldier_id,))
    delete_duty = "DELETE FROM Duty WHERE SoldierID = ? AND Date >= ?"
    db.execute(delete_duty, (soldier_id,date))
    delete_leave = "DELETE FROM Leave WHERE SoldierID = ? AND DateTo >= ?"
    db.execute(delete_leave, (soldier_id,date))
    delete_course = "DELETE FROM OnCourse WHERE SoldierID = ? AND DateTo >= ?"
    db.execute(delete_course, (soldier_id,date))
    delete_ration = "DELETE FROM RationType WHERE SoldierID = ?"
    db.execute(delete_ration, (soldier_id,))

    delete_attendance = "DELETE FROM Attendance WHERE SoldierID = ?"
    delete_info = "DELETE FROM SoldierInfo WHERE SoldierID = ?"
    db.execute(delete_attendance, (soldier_id,))
    db.execute(delete_info, (soldier_id,))
    db.commit()
    db.close()

def update_db_info(soldier_info,current_soldier_id_list):
    db = sqlite3.connect(db_path)
    # To update when new soldierID is added
    soldier_id = soldier_info[1]
    query = "SELECT * FROM SoldierInfo WHERE SoldierID = ?"
    cursor = db.execute(query, (soldier_id,))
    data = cursor.fetchone()
    new_soldier_id = None
    # If SoldierID is not in DB (new record is being added)
    if data == None:
        query = """INSERT INTO SoldierInfo
        (SoldierID, Rank, Name, PLT, SCT, GRP, StayOut)
        VALUES
        (?, ?, ?, ?, ?, ?, ?)
        """
        rank = soldier_info[2]
        name = soldier_info[3]
        sct = soldier_info[5]
        if soldier_info[4] == "":
            plt = "P{}S{}".format(sct[0],sct[1])
        else:
            plt = soldier_info[4]
        grp = soldier_info[6]
        stayout = str(soldier_info[7] == "Yes")
        if soldier_id == "":
            soldier_id = utils.generate_soldierID("3SIR19A",name,current_soldier_id_list)
            current_soldier_id_list.append(soldier_id)
            new_soldier_id = soldier_id
        db.execute(query, (soldier_id,rank,name,plt,sct,grp,stayout))
        query = "INSERT INTO Attendance (SoldierID, InCamp) VALUES (?, ?)"
        db.execute(query, (soldier_id, "False"))
    # SoldierID is part of DB (existing record is being updated)
    else:
        query = """
        UPDATE SoldierInfo
        SET Rank = ?, Name = ?, PLT = ?, SCT = ?, GRP = ?, StayOut = ?
        WHERE SoldierID = ?
        """
        rank = soldier_info[2]
        name = soldier_info[3]
        plt = soldier_info[4]
        sct = soldier_info[5]
        grp = soldier_info[6]
        stayout = str(soldier_info[7] == "Yes")
        db.execute(query, (rank,name,plt,sct,grp,stayout,soldier_id))
    db.commit()
    db.close()
    return new_soldier_id

#### FUNCTION: UPDATE DUTY DB ACCORDING TO GOOGLESHEET ####

def update_db_from_gsheet_duty():
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url(sheet_url)
    worksheets = sh.worksheets()
    paradestate_sh = gc.open_by_url("sheet_url?usp=sharing")
    paradestate_worksheet = paradestate_sh.get_worksheet(0)
    # clear_duty()
    for worksheet in worksheets:
        insert_data = get_duty(worksheet)
        if insert_data and len(insert_data) > 0:
            insert_db_duty(insert_data,paradestate_worksheet)

def clear_duty():
    db = sqlite3.connect(db_path)
    tz = pytz.timezone('Asia/Singapore')
    now = datetime.now(tz)
    query = "DELETE FROM Duty WHERE Date = ?"
    db.execute(query, (now.strftime("%y%m%d"),))
    db.commit()
    db.close()


def get_duty(worksheet):
    db = sqlite3.connect(db_path)
    name_list = worksheet.col_values(2)
    date_list = worksheet.row_values(1)
    to_insert = []
    duty_dict = {"COS":"COS Duty","GD":"Guard Duty","DOS":"DOS","DOO":"DOO"}
    tz = pytz.timezone('Asia/Singapore')
    now = datetime.now(tz)
    today = now.strftime("%d/%m/%y")
    try:
        date_index = date_list.index(today)
    except:
        return
    duty_records = worksheet.col_values(date_index+1)
    for i, duty in enumerate(duty_records):
        if duty in duty_dict.keys():
            converted_date = now.strftime("%y%m%d")
            select_query = "SELECT SoldierID FROM SoldierInfo WHERE Name LIKE ?"
            cursor = db.execute(select_query, ("%"+name_list[i]+"%",))
            data = cursor.fetchone()
            soldier_id = data[0]
            insert_record = (soldier_id,converted_date,duty_dict[duty],"")
            to_insert.append(insert_record)
    db.close()
    return to_insert

def insert_db_duty(data, worksheet):
    id_list = worksheet.col_values(2)
    date_list = worksheet.row_values(2)
    to_update_cells = []
    db = sqlite3.connect(db_path)
    insert_query = """INSERT INTO Duty
                    (SoldierID,Date,DutyType,Remarks)
                    VALUES
                    (?,?,?,?)"""
    for row in data:
        try:
            db.execute(insert_query, row)
        except:
            pass
        date = row[1]
        converted_date = utils.convert_date_ymd_db(date)
        soldier_row = utils.get_index(row[0], id_list) + 1
        date_col = utils.get_index(converted_date, date_list) + 1
        to_update_cells.append(Cell(row=soldier_row, col=date_col, value=row[2]))
    if len(to_update_cells) > 0:
        worksheet.update_cells(to_update_cells)
    db.commit()
    db.close()


def update_db_from_gsheet_trooper_duty():
    gc = SERVICE_ACCOUNT
    gd_sh = gc.open_by_url(sheet_url)
    worksheet_title = utils.get_now().strftime("%b %y").capitalize()
    gd_worksheet = gd_sh.worksheet(worksheet_title)
    insert_data = get_trooper_duty(gd_worksheet)
    if insert_data and len(insert_data) > 0:
        update_gsheet_and_db_duty(insert_data)

def get_trooper_duty(worksheet):
    db = sqlite3.connect(db_path)
    name_list = worksheet.col_values(4)
    date_list = worksheet.col_values(1)
    unit_list = worksheet.col_values(5)
    to_insert = []
    tz = pytz.timezone('Asia/Singapore')
    now = datetime.now(tz)
    today = now.strftime("%-d-%b-%Y")
    converted_date = now.strftime("%d%m%y")
    try:
        date_index = date_list.index(today) + 2
        unit = unit_list[date_index]
    except:
        return
    while date_index < len(unit_list) and unit == unit_list[date_index]:
        if name_list[date_index] == "":
            date_index += 1
            continue
        insert_record = "{} {} {}".format(name_list[date_index],converted_date,"Guard Duty")
        to_insert.append(insert_record)
        date_index += 1
    db.close()
    return to_insert

def update_db_from_gsheet_leave_off():
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url(sheet_url)
    worksheets = sh.worksheets()
    paradestate_sh = gc.open_by_url("sheet_url?usp=sharing")
    paradestate_worksheet = paradestate_sh.get_worksheet(0)
    for worksheet in worksheets:
        insert_data = get_leave_off(worksheet)
        if insert_data and len(insert_data) > 0:
            insert_db_leave_off(insert_data,paradestate_worksheet)

def get_leave_off(worksheet):
    db = sqlite3.connect(db_path)
    name_list = worksheet.col_values(2)
    all_records = worksheet.get_all_values()
    date_list = all_records[0]
    to_insert = []
    leave_dict = {"Leave":"LOCAL","Off":"OFF"}
    tz = pytz.timezone('Asia/Singapore')
    # update leaves 3 days in advance
    now = datetime.now(tz) + timedelta(days=3)
    today = now.strftime("%d/%m/%y")
    try:
        date_index = date_list.index(today)
    except:
        return
    leave_records = worksheet.col_values(date_index+1)
    for i, leave in enumerate(leave_records):
        if leave in leave_dict.keys():
            current = leave
            current_date_index = date_index
            while current in leave_dict.keys():
                current_date_index += 1
                current = all_records[i][current_date_index]
            start_date = now.strftime("%y%m%d")
            end_date = datetime.strptime(date_list[current_date_index], "%d/%m/%y").strftime("%y%m%d")
            select_query = "SELECT SoldierID FROM SoldierInfo WHERE Name LIKE ?"
            cursor = db.execute(select_query, ("%"+name_list[i]+"%",))
            data = cursor.fetchone()
            soldier_id = data[0]
            check_query = "SELECT * FROM Leave WHERE SoldierID = ? AND DateTo = ?"
            cursor = db.execute(check_query, (soldier_id, end_date))
            data = cursor.fetchall()
            if len(data) == 0:
                insert_record = (soldier_id,leave_dict[leave],start_date,end_date,"")
                to_insert.append(insert_record)
    db.close()
    return to_insert

def insert_db_leave_off(data, worksheet):
    id_list = worksheet.col_values(2)
    date_list = worksheet.row_values(2)
    to_update_cells = []
    to_batch_update = []
    db = sqlite3.connect(db_path)
    insert_query = """INSERT INTO Leave
                (SoldierID,Country,DateFrom,DateTo,Remarks)
                VALUES
                (?,?,?,?,?)"""
    for row in data:
        try:
            db.execute(insert_query, row)
        except:
            pass
        country = row[1]
        date_from = row[2]
        date_to = row[3]
        soldier_row = utils.get_index(row[0], id_list) + 1
        if date_from == date_to:
            date_from_col = utils.get_index(utils.convert_date_dmy_db(date_from), date_list) + 1
            date_to_col = utils.get_index(utils.convert_date_dmy_db(date_to), date_list) + 1
            date_from_A1 = rowcol_to_a1(soldier_row,date_from_col)
            date_to_A1 = rowcol_to_a1(soldier_row,date_to_col)

            update_range = "{}:{}".format(date_from_A1,date_to_A1)
            number_of_col = date_to_col - date_from_col + 1
            if country.upper() == "LOCAL":
                update_dict = {"range": update_range, "values": [["Local Leave"]*number_of_col]}
            elif country.upper() == "OFF":
                update_dict = {"range": update_range, "values": [["Off"]*number_of_col]}
            else:
                update_dict = {"range": update_range, "values": [["Overseas Leave"]*number_of_col]}
            to_batch_update.append(update_dict)
        else:
            converted_date = utils.convert_date_dmy_db(date_to)
            date_col = utils.get_index(converted_date, date_list) + 1
            if country.upper() == "LOCAL":
                to_update_cells.append(Cell(row=soldier_row, col=date_col, value="Local Leave"))
            elif country.upper() == "OFF":
                to_update_cells.append(Cell(row=soldier_row, col=date_col, value="Off"))
            else:
                to_update_cells.append(Cell(row=soldier_row, col=date_col, value="Overseas Leave"))
    worksheet.batch_update(to_batch_update)
    if len(to_update_cells) > 0:
        worksheet.update_cells(to_update_cells)
    db.commit()
    db.close()



#### FUNCTION: UPDATE GOOGLE SHEET & DB FROM MESSAGE ####
def update_gsheet_and_db_duty(msg):
    """
    MSG FORMAT:
    RANK NAME DATE DUTYTYPE
    E.G.: 3SG MATHIS 261223-281223 MC
    """
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    db = sqlite3.connect(db_path)

    name_list = worksheet.col_values(4)
    date_list = worksheet.row_values(2)
    sct_list = worksheet.col_values(6)

    date_dict = {}
    to_batch_update = []
    to_update_cells = []

    result_msg = []

    # msg = msg.strip()
    # msg = msg.split("\n")
    unformatted_msg = utils.unformat_msg(msg, "duty")
    for soldier_info in unformatted_msg:
        name = soldier_info["NAME"].upper()
        dutyType = soldier_info["DETAILS"]
        date = soldier_info["DATE"]
        date = date.split("-")
        remarks = soldier_info["REMARKS"]

        id_4d = soldier_info["4D"]
        try:
            if id_4d != "":
                soldier_row = utils.get_index(id_4d,sct_list) + 1
            else:
                soldier_row = utils.get_name_index(name, name_list) + 1
        except utils.NameConflict as names:
            raise
        except:
            raise NotFound

        soldier_name = name_list[soldier_row-1]
        cursor = db.execute("SELECT SoldierID FROM SoldierInfo WHERE Name = ?", (soldier_name,))
        data = cursor.fetchone()
        soldier_id = data[0]
        if soldier_info["DELETE"]:
            query = '''
            DELETE FROM Duty
            WHERE SoldierID = ?
            AND Date = ?
            '''
            date = date[0]
            converted_date = utils.convert_date_dmy_db(date)
            date_col = utils.get_index(converted_date, date_list) + 1
            to_update_cells.append(Cell(row=soldier_row, col=date_col, value=""))
            db.execute(query, (soldier_id,utils.convert_date_dmy_ymd(date)))
        else:
            query = '''
            INSERT INTO Duty
            (SoldierID,Date,DutyType,Remarks)
            VALUES
            (?,?,?,?)
            '''
            # Single Day Duty
            date = date[0]
            converted_date = utils.convert_date_dmy_db(date)
            date_col = utils.get_index(converted_date, date_list) + 1
            to_update_cells.append(Cell(row=soldier_row, col=date_col, value=dutyType))
            try:
                db.execute(query, (soldier_id,utils.convert_date_dmy_ymd(date),dutyType,remarks))
                result_msg.append(soldier_name)
            except:
                pass
    db.commit()
    db.close()
    worksheet.batch_update(to_batch_update)
    if len(to_update_cells) > 0:
        worksheet.update_cells(to_update_cells)
    return result_msg

#### FUNCTION: UPDATE GOOGLE SHEET FROM MESSAGE ####
def update_gsheet_and_db_leaves(msg):
    """
    MSG FORMAT:
    RANK NAME DATE TYPE
    E.G.: 3SG MATHIS 261223-281223 LOCAL
    """
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    db = sqlite3.connect(db_path)
    # db.execute("DELETE FROM Leave")

    name_list = worksheet.col_values(4)
    date_list = worksheet.row_values(2)
    sct_list = worksheet.col_values(6)

    to_batch_update = []
    to_update_cells = []

    result_msg = []

    # msg = msg.strip()
    # msg = msg.split("\n")
    unformatted_msg = utils.unformat_msg(msg, "leave")
    for soldier_info in unformatted_msg:
        name = soldier_info["NAME"].upper()
        country = soldier_info["DETAILS"]
        date = soldier_info["DATE"]
        date = date.split("-")
        remarks = soldier_info["REMARKS"]

        id_4d = soldier_info["4D"]
        try:
            if id_4d != "":
                soldier_row = utils.get_index(id_4d,sct_list) + 1
            else:
                soldier_row = utils.get_name_index(name, name_list) + 1
        except utils.NameConflict as names:
            raise
        except:
            raise NotFound

        soldier_name = name_list[soldier_row-1]
        cursor = db.execute("SELECT SoldierID FROM SoldierInfo WHERE Name = ?", (soldier_name,))
        data = cursor.fetchone()
        soldier_id = data[0]
        # DELETE query
        if soldier_info["DELETE"]:
            query = '''
            DELETE FROM Leave
            WHERE SoldierID = ?
            AND Country = ?
            AND DateFrom = ?
            AND DateTo = ?
            '''
            # Multiple Day Leave (DateFrom & DateTo)
            if len(date) == 2:
                date_from = date[0]
                date_to = date[1]

                date_from_col = utils.get_index(utils.convert_date_dmy_db(date_from), date_list) + 1
                date_to_col = utils.get_index(utils.convert_date_dmy_db(date_to), date_list) + 1
                date_from_A1 = rowcol_to_a1(soldier_row,date_from_col)
                date_to_A1 = rowcol_to_a1(soldier_row,date_to_col)

                update_range = "{}:{}".format(date_from_A1,date_to_A1)
                number_of_col = date_to_col - date_from_col + 1

                update_dict = {"range": update_range, "values": [[""]*number_of_col]}
                to_batch_update.append(update_dict)
                db.execute(query, (soldier_id, country, utils.convert_date_dmy_ymd(date_from),utils.convert_date_dmy_ymd(date_to)))
            # Single Day Leave
            else:
                date = date[0]
                converted_date = utils.convert_date_dmy_db(date)
                date_col = utils.get_index(converted_date, date_list) + 1

                to_update_cells.append(Cell(row=soldier_row, col=date_col, value=""))
                db.execute(query, (soldier_id, country, utils.convert_date_dmy_ymd(date),utils.convert_date_dmy_ymd(date)))
        else:
            query = '''
            INSERT INTO Leave
            (SoldierID,Country,DateFrom,DateTo,Remarks)
            VALUES
            (?,?,?,?,?)
            '''
            # Multiple Day Leave (DateFrom & DateTo)
            if len(date) == 2:
                date_from = date[0]
                date_to = date[1]

                date_from_col = utils.get_index(utils.convert_date_dmy_db(date_from), date_list) + 1
                date_to_col = utils.get_index(utils.convert_date_dmy_db(date_to), date_list) + 1
                date_from_A1 = rowcol_to_a1(soldier_row,date_from_col)
                date_to_A1 = rowcol_to_a1(soldier_row,date_to_col)

                update_range = "{}:{}".format(date_from_A1,date_to_A1)
                number_of_col = date_to_col - date_from_col + 1
                if country.upper() == "LOCAL" or country == "":
                    update_dict = {"range": update_range, "values": [["Local Leave"]*number_of_col]}
                    to_batch_update.append(update_dict)
                    db.execute(query, (soldier_id, "LOCAL", utils.convert_date_dmy_ymd(date_from),utils.convert_date_dmy_ymd(date_to),remarks))
                elif country.upper() == "OFF":
                    update_dict = {"range": update_range, "values": [["Off"]*number_of_col]}
                    to_batch_update.append(update_dict)
                    db.execute(query, (soldier_id, country, utils.convert_date_dmy_ymd(date_from),utils.convert_date_dmy_ymd(date_to),remarks))
                else:
                    update_dict = {"range": update_range, "values": [["Overseas Leave"]*number_of_col]}
                    to_batch_update.append(update_dict)
                    db.execute(query, (soldier_id, country, utils.convert_date_dmy_ymd(date_from),utils.convert_date_dmy_ymd(date_to),remarks))
            # Single Day Leave
            else:
                date = date[0]
                converted_date = utils.convert_date_dmy_db(date)
                date_col = utils.get_index(converted_date, date_list) + 1
                if country.upper() == "LOCAL" or country == "":
                    to_update_cells.append(Cell(row=soldier_row, col=date_col, value="Local Leave"))
                    db.execute(query, (soldier_id, country,utils.convert_date_dmy_ymd(date),utils.convert_date_dmy_ymd(date),remarks))
                elif country.upper() == "OFF":
                    to_update_cells.append(Cell(row=soldier_row, col=date_col, value="Off"))
                    db.execute(query, (soldier_id, country,utils.convert_date_dmy_ymd(date),utils.convert_date_dmy_ymd(date),remarks))
                else:
                    to_update_cells.append(Cell(row=soldier_row, col=date_col, value="Overseas Leave"))
                    db.execute(query, (soldier_id, country,utils.convert_date_dmy_ymd(date),utils.convert_date_dmy_ymd(date),remarks))
            result_msg.append(soldier_name)
    db.commit()
    db.close()
    worksheet.batch_update(to_batch_update)
    if len(to_update_cells) > 0:
        worksheet.update_cells(to_update_cells)
    return result_msg

#### FUNCTION: UPDATE GOOGLE SHEET & DB FROM MESSAGE ####
def update_gsheet_and_db_ma(msg):
    """
    MSG FORMAT:
    RANK NAME DATE REMARKS
    E.G.: 3SG MATHIS 261223-281223 MC
    """
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    db = sqlite3.connect(db_path)
    # db.execute("DELETE FROM Duty")

    result_msg = []

    name_list = worksheet.col_values(4)
    date_list = worksheet.row_values(2)
    sct_list = worksheet.col_values(6)

    to_batch_update = []
    to_update_cells = []

    # msg = msg.strip()
    # msg = msg.split("\n")
    unformatted_msg = utils.unformat_msg(msg, "ma")
    for soldier_info in unformatted_msg:
        name = soldier_info["NAME"].upper()
        details = soldier_info["DETAILS"]
        date = soldier_info["DATE"]
        date = date.split("-")
        remarks = soldier_info["REMARKS"]
        if len(details) > 0:
            remarks = details

        id_4d = soldier_info["4D"]
        try:
            if id_4d != "":
                soldier_row = utils.get_index(id_4d,sct_list) + 1
            else:
                soldier_row = utils.get_name_index(name, name_list) + 1
        except utils.NameConflict as names:
            raise
        except:
            raise NotFound

        soldier_name = name_list[soldier_row-1]
        cursor = db.execute("SELECT SoldierID FROM SoldierInfo WHERE Name = ?", (soldier_name,))
        data = cursor.fetchone()
        soldier_id = data[0]
        if soldier_info["DELETE"]:
            query = '''
            DELETE FROM MedicalAppointment
            WHERE SoldierID = ?
            AND Date = ?
            '''
            date = date[0]
            converted_date = utils.convert_date_dmy_db(date)
            date_col = utils.get_index(converted_date, date_list) + 1
            to_update_cells.append(Cell(row=soldier_row, col=date_col, value=""))
            db.execute(query, (soldier_id,utils.convert_date_dmy_ymd(date)))
        else:
            query = '''
            INSERT INTO MedicalAppointment
            (SoldierID,Date,Remarks)
            VALUES
            (?,?,?)
            '''
            # Single Day Duty
            date = date[0]
            converted_date = utils.convert_date_dmy_db(date)
            date_col = utils.get_index(converted_date, date_list) + 1
            to_update_cells.append(Cell(row=soldier_row, col=date_col, value="MA"))
            db.execute(query, (soldier_id,utils.convert_date_dmy_ymd(date),remarks))
            result_msg.append(soldier_name)
    db.commit()
    db.close()
    worksheet.batch_update(to_batch_update)
    if len(to_update_cells) > 0:
        worksheet.update_cells(to_update_cells)
    return result_msg

#### FUNCTION: UPDATE GOOGLE SHEET & DB FROM MESSAGE ####
def check_ms_num_days(db:sqlite3.Connection, soldier_id, num_days, detail):
    query = """SELECT DateFrom, DateTo
            FROM MedicalStatus
            WHERE SoldierID = ?
            AND MedicalStatus = ?
            ORDER BY DateFrom DESC"""
    cursor = db.execute(query, (soldier_id, detail))
    data = cursor.fetchall()
    for status_row in data:
        days = utils.format_num_days(status_row[0], status_row[1])
        if days == num_days:
            return utils.convert_date_ymd_dmy(status_row[0]), utils.convert_date_ymd_dmy(status_row[1])
    return None

def update_gsheet_and_db_ms(msg):
    """
    MSG FORMAT:
    RANK NAME DATE TYPE
    E.G.: 3SG MATHIS 261223-281223 MC
    """
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    db = sqlite3.connect(db_path)
    # db.execute("DELETE FROM MedicalStatus")

    name_list = worksheet.col_values(4)
    date_list = worksheet.row_values(2)
    sct_list = worksheet.col_values(6)

    to_batch_update = []
    to_update_cells = []

    result_msg = []

    # msg = msg.strip()
    # msg = msg.split("\n")
    unformatted_msg = utils.unformat_msg(msg, "ms")
    for soldier_info in unformatted_msg:
        name = soldier_info["NAME"].upper()
        status = soldier_info["DETAILS"].strip()
        date = soldier_info["DATE"]
        date = date.split("-")
        remarks = soldier_info["REMARKS"]

        id_4d = soldier_info["4D"]
        try:
            if id_4d != "":
                soldier_row = utils.get_index(id_4d,sct_list) + 1
            else:
                soldier_row = utils.get_name_index(name, name_list) + 1
        except utils.NameConflict as names:
            raise
        except:
            raise NotFound

        if len(status) == 0 and len(remarks) == 0:
            raise NoDetail

        soldier_name = name_list[soldier_row-1]
        cursor = db.execute("SELECT SoldierID FROM SoldierInfo WHERE Name = ?", (soldier_name,))
        data = cursor.fetchone()
        soldier_id = data[0]

        if soldier_info["DELETE"]:
            if len(date) == 2:
                check_num_days = utils.format_num_days(utils.convert_date_dmy_ymd(date[0]),
                                                    utils.convert_date_dmy_ymd(date[1]))
            else:
                check_num_days = "1D"
            check = check_ms_num_days(db, soldier_id, check_num_days, status)
            if soldier_info["D"] and check:
                if len(date) == 2:
                    date_from, date_to = check
                else:
                    date = check[0]
            else:
                if len(date) == 2:
                    date_from = date[0]
                    date_to = date[1]
                else:
                    date = date[0]
            query = '''
            DELETE FROM MedicalStatus
            WHERE SoldierID = ?
            AND MedicalStatus = ?
            AND DateFrom = ?
            AND DateTo = ?
            '''
            if status.upper() == "MC":
                # update sheets if MC
                if len(date) == 2:
                    # update multiple days on sheet with range
                    date_from_col = utils.get_index(utils.convert_date_dmy_db(date_from), date_list) + 1
                    date_to_col = utils.get_index(utils.convert_date_dmy_db(date_to), date_list) + 1
                    date_from_A1 = rowcol_to_a1(soldier_row,date_from_col)
                    date_to_A1 = rowcol_to_a1(soldier_row,date_to_col)

                    update_range = "{}:{}".format(date_from_A1,date_to_A1)
                    number_of_col = date_to_col - date_from_col + 1

                    update_dict = {"range": update_range, "values": [[""]*number_of_col]}
                    to_batch_update.append(update_dict)
                    date_from = utils.convert_date_dmy_ymd(date_from)
                    date_to = utils.convert_date_dmy_ymd(date_to)
                    db.execute(query, (soldier_id, status.upper(), date_from, date_to))
                else:
                    # update single days on sheet with cell
                    converted_date = utils.convert_date_dmy_db(date)
                    date_col = utils.get_index(converted_date, date_list) + 1
                    to_update_cells.append(Cell(row=soldier_row, col=date_col, value=""))
                    date_from = utils.convert_date_dmy_ymd(date)
                    date_to = utils.convert_date_dmy_ymd(date)
                    db.execute(query, (soldier_id, status.upper(), date_from, date_to))
            else:
                if len(date) == 2:
                    date_from = utils.convert_date_dmy_ymd(date_from)
                    date_to = utils.convert_date_dmy_ymd(date_to)
                    db.execute(query, (soldier_id, status, date_from, date_to))
                # Single Day Status
                else:
                    converted_date = utils.convert_date_dmy_db(date)
                    date_from = utils.convert_date_dmy_ymd(date)
                    date_to = utils.convert_date_dmy_ymd(date)
                    db.execute(query, (soldier_id, status, date_from, date_to))
        else:
            query = "SELECT Remarks FROM ReportingSick WHERE SoldierID = ?"
            cursor = db.execute(query, (soldier_id,))
            data = cursor.fetchone()
            if remarks == "" and data != None:
                remarks = data[0]
            query = "DELETE FROM ReportingSick WHERE SoldierID = ?"
            db.execute(query, (soldier_id,))

            query = '''
            INSERT INTO MedicalStatus
            (SoldierID,MedicalStatus,DateFrom,DateTo,Remarks)
            VALUES
            (?,?,?,?,?)
            '''
            # only updates sheet if mc
            if status.strip().upper() == "MC":
                # Multiple Day Leave (DateFrom & DateTo)
                if len(date) == 2:
                    date_from = date[0]
                    date_to = date[1]

                    date_from_col = utils.get_index(utils.convert_date_dmy_db(date_from), date_list) + 1
                    date_to_col = utils.get_index(utils.convert_date_dmy_db(date_to), date_list) + 1
                    date_from_A1 = rowcol_to_a1(soldier_row,date_from_col)
                    date_to_A1 = rowcol_to_a1(soldier_row,date_to_col)

                    update_range = "{}:{}".format(date_from_A1,date_to_A1)
                    number_of_col = date_to_col - date_from_col + 1

                    update_dict = {"range": update_range, "values": [["MC"]*number_of_col]}
                    to_batch_update.append(update_dict)
                    date_from = utils.convert_date_dmy_ymd(date_from)
                    date_to = utils.convert_date_dmy_ymd(date_to)
                    db.execute(query, (soldier_id, status.upper(), date_from, date_to, remarks))
                    result_msg.append((soldier_name, utils.format_num_days(date_from, date_to), status, utils.convert_date_ymd_dmy_slash(date_from), utils.convert_date_ymd_dmy_slash(date_to)))
                # Single Day MC
                else:
                    date = date[0]
                    converted_date = utils.convert_date_dmy_db(date)
                    date_col = utils.get_index(converted_date, date_list) + 1
                    to_update_cells.append(Cell(row=soldier_row, col=date_col, value="MC"))
                    date_from = utils.convert_date_dmy_ymd(date)
                    date_to = utils.convert_date_dmy_ymd(date)
                    db.execute(query, (soldier_id, status.upper(), date_from, date_to, remarks))
                    result_msg.append((soldier_name, utils.format_num_days(date_from, date_to), status, utils.convert_date_ymd_dmy_slash(date_from), utils.convert_date_ymd_dmy_slash(date_to)))
            # updates db for all status
            else:
                if status.strip().lower() == "rib" or status.strip().lower() == "rest in bunk" or status.strip().lower() == "rest-in-bunk":
                    status = "RIB"
                # Multiple Day Status
                if date[0].upper() in "PERMANENT":
                    date_from = "PERMANENT"
                    date_to = "PERMANENT"
                    db.execute(query, (soldier_id, status, date_from, date_to, remarks))
                    result_msg.append((soldier_name, "PERMANENT", status, "PERMANENT", "PERMANENT"))
                elif len(date) == 2:
                    date_from = date[0]
                    date_to = date[1]
                    date_from = utils.convert_date_dmy_ymd(date_from)
                    date_to = utils.convert_date_dmy_ymd(date_to)
                    db.execute(query, (soldier_id, status, date_from, date_to, remarks))
                    result_msg.append((soldier_name, utils.format_num_days(date_from, date_to), status, utils.convert_date_ymd_dmy_slash(date_from), utils.convert_date_ymd_dmy_slash(date_to)))
                # Single Day Status
                else:
                    date = date[0]
                    converted_date = utils.convert_date_dmy_db(date)
                    date_from = utils.convert_date_dmy_ymd(date)
                    date_to = utils.convert_date_dmy_ymd(date)
                    db.execute(query, (soldier_id, status, date_from, date_to, remarks))
                    result_msg.append((soldier_name, utils.format_num_days(date_from, date_to), status, utils.convert_date_ymd_dmy_slash(date_from), utils.convert_date_ymd_dmy_slash(date_to)))

    worksheet.batch_update(to_batch_update)
    if len(to_update_cells) > 0:
        worksheet.update_cells(to_update_cells)
    db.commit()
    db.close()
    return result_msg



#### FUNCTION: UPDATE GOOGLE SHEET & DB FROM MESSAGE ####
def update_gsheet_and_db_course(msg):
    """
    MSG FORMAT:
    RANK NAME DATE TYPE
    E.G.: 3SG MATHIS 261223-281223 BVOC
    """
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    db = sqlite3.connect(db_path)

    name_list = worksheet.col_values(4)
    date_list = worksheet.row_values(2)
    sct_list = worksheet.col_values(6)

    to_batch_update = []
    to_update_cells = []

    result_msg = []

    unformatted_msg = utils.unformat_msg(msg, "course")
    for soldier_info in unformatted_msg:
        name = soldier_info["NAME"].upper()
        course = soldier_info["DETAILS"]
        date = soldier_info["DATE"]
        date = date.split("-")
        remarks = soldier_info["REMARKS"]

        id_4d = soldier_info["4D"]
        try:
            if id_4d != "":
                soldier_row = utils.get_index(id_4d,sct_list) + 1
            else:
                soldier_row = utils.get_name_index(name, name_list) + 1
        except utils.NameConflict as names:
            raise
        except:
            raise NotFound

        soldier_name = name_list[soldier_row-1]
        cursor = db.execute("SELECT SoldierID FROM SoldierInfo WHERE Name = ?", (soldier_name,))
        data = cursor.fetchone()
        soldier_id = data[0]
        if soldier_info["DELETE"]:
            query = '''
            DELETE FROM OnCourse
            WHERE SoldierID = ?
            AND CourseName = ?
            AND DateFrom = ?
            AND DateTo = ?
            '''
            # Multiple Day Course (DateFrom & DateTo)
            if len(date) == 2:
                date_from = date[0]
                date_to = date[1]

                date_from_col = utils.get_index(utils.convert_date_dmy_db(date_from), date_list) + 1
                date_to_col = utils.get_index(utils.convert_date_dmy_db(date_to), date_list) + 1
                date_from_A1 = rowcol_to_a1(soldier_row,date_from_col)
                date_to_A1 = rowcol_to_a1(soldier_row,date_to_col)

                update_range = "{}:{}".format(date_from_A1,date_to_A1)
                number_of_col = date_to_col - date_from_col + 1

                update_dict = {"range": update_range, "values": [[""]*number_of_col]}
                to_batch_update.append(update_dict)
                db.execute(query, (soldier_id,course,utils.convert_date_dmy_ymd(date_from),utils.convert_date_dmy_ymd(date_to)))
            # Single Day Course
            else:
                date = date[0]
                converted_date = utils.convert_date_dmy_db(date)
                date_col = utils.get_index(converted_date, date_list) + 1
                to_update_cells.append(Cell(row=soldier_row, col=date_col, value=""))
                db.execute(query, (soldier_id,course,utils.convert_date_dmy_ymd(date),utils.convert_date_dmy_ymd(date)))
        # OOC Query
        elif soldier_info["OOC"]:
            # OOC Date
            ooc_date = date[0]
            # get originial date_to from db
            query = """
            SELECT DateTo
            FROM OnCourse
            WHERE SoldierID = ?
            AND CourseName = ?
            ORDER BY DateFrom DESC"""
            cursor = db.execute(query, (soldier_id,course))
            data = cursor.fetchone()
            old_date_to = data[0]
            # get range of cells to update (from ooc date to original date_to)
            date_from_col = utils.get_index(utils.convert_date_dmy_db(ooc_date), date_list) + 1
            date_to_col = utils.get_index(utils.convert_date_ymd_db(old_date_to), date_list) + 1
            date_from_A1 = rowcol_to_a1(soldier_row,date_from_col)
            date_to_A1 = rowcol_to_a1(soldier_row,date_to_col)

            get_range = "{}:{}".format(date_from_A1,date_to_A1)
            current_records = worksheet.batch_get((get_range,))[0][0]

            for i in range(len(current_records)):
                if current_records[i] == "On Course":
                    date_col = i + date_from_col
                    to_update_cells.append(Cell(row=soldier_row, col=date_col, value=""))
            # update db set end date
            query = """
            UPDATE OnCourse
            SET DateTo = ?
            WHERE SoldierID = ?
            AND CourseName = ?"""
            db.execute(query, (ooc_date,soldier_id,course))
            result_msg.append(soldier_name)
        else:
            query = '''
            INSERT INTO OnCourse
            (SoldierID,CourseName,DateFrom,DateTo,Remarks)
            VALUES
            (?,?,?,?,?)
            '''
            # Multiple Day Course (DateFrom & DateTo)
            if len(date) == 2:
                date_from = date[0]
                date_to = date[1]

                date_from_col = utils.get_index(utils.convert_date_dmy_db(date_from), date_list) + 1
                date_to_col = utils.get_index(utils.convert_date_dmy_db(date_to), date_list) + 1
                date_from_A1 = rowcol_to_a1(soldier_row,date_from_col)
                date_to_A1 = rowcol_to_a1(soldier_row,date_to_col)

                update_range = "{}:{}".format(date_from_A1,date_to_A1)
                number_of_col = date_to_col - date_from_col + 1

                update_dict = {"range": update_range, "values": [["On Course"]*number_of_col]}
                to_batch_update.append(update_dict)
                db.execute(query, (soldier_id,course,utils.convert_date_dmy_ymd(date_from),utils.convert_date_dmy_ymd(date_to),remarks))
                result_msg.append(soldier_name)
            # Single Day Course
            else:
                date = date[0]
                converted_date = utils.convert_date_dmy_db(date)
                date_col = utils.get_index(converted_date, date_list) + 1
                to_update_cells.append(Cell(row=soldier_row, col=date_col, value="On Course"))
                db.execute(query, (soldier_id,course,utils.convert_date_dmy_ymd(date),utils.convert_date_dmy_ymd(date),remarks))
                result_msg.append(soldier_name)
    db.commit()
    db.close()
    worksheet.batch_update(to_batch_update)
    if len(to_update_cells) > 0:
        worksheet.update_cells(to_update_cells)
    return result_msg

#### FUNCTION: UPDATE GOOGLE SHEET & DB FROM MESSAGE ####
def update_gsheet_and_db_others(msg):
    """
    MSG FORMAT:
    RANK NAME InCamp/NotInCamp Date(Optional) REASON REMARKS:(Optional)
    E.G.: 3SG MATHIS NotInCamp/InCamp 150124-160124 RSO REMARKS: xxxx
    """
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    db = sqlite3.connect(db_path)

    name_list = worksheet.col_values(4)
    date_list = worksheet.row_values(2)
    sct_list = worksheet.col_values(6)

    to_batch_update = []
    to_update_cells = []

    result_msg = []

    unformatted_msg = utils.unformat_msg(msg, "others")
    for soldier_info in unformatted_msg:
        name = soldier_info["NAME"].upper()
        reason = soldier_info["DETAILS"]
        date = soldier_info["DATE"]
        date = date.split("-")
        inCamp = soldier_info["InCamp"]
        remarks = soldier_info["REMARKS"]

        # get row number of soldier
        id_4d = soldier_info["4D"]
        try:
            if id_4d != "":
                soldier_row = utils.get_index(id_4d,sct_list) + 1
            else:
                soldier_row = utils.get_name_index(name, name_list) + 1
        except utils.NameConflict as names:
            raise
        except:
            raise NotFound

        # get name of soldier from sheets
        soldier_name = name_list[soldier_row-1]
        cursor = db.execute("SELECT SoldierID FROM SoldierInfo WHERE Name = ?", (soldier_name,))
        data = cursor.fetchone()
        # get soldierID from DB
        soldier_id = data[0]
        if soldier_info["DELETE"]:
            if utils.is_date(date[0]):
                query = '''
                DELETE FROM Others
                WHERE SoldierID = ?
                AND Reason = ?
                AND DateFrom = ?
                AND DateTo = ?
                '''
                # Multiple Day Reason
                if len(date) == 2:
                    date_from = date[0]
                    date_to = date[1]
                    # only update sheets if reason is to be recorded
                    db.execute(query, (soldier_id,reason,utils.convert_date_dmy_ymd(date_from),utils.convert_date_dmy_ymd(date_to)))
                elif date[0] == "PERMANENT":
                    date = date[0]
                    db.execute(query, (soldier_id,reason,date,date))
                # Single Day Reason
                else:
                    date = date[0]
                    # only update sheets if reason is to be recorded
                    db.execute(query, (soldier_id,reason,utils.convert_date_dmy_ymd(date),utils.convert_date_dmy_ymd(date)))
            # case where date is not inputed (temporary reason)
            else:
                query = '''
                DELETE FROM Others
                WHERE SoldierID = ?
                AND Reason = ?
                '''
                db.execute(query, (soldier_id,reason))
        else:
            query = '''
            INSERT INTO Others
            (SoldierID,Reason,DateFrom,DateTo,InCamp,Remarks)
            VALUES
            (?,?,?,?,?,?)
            '''
            # case where date is inputed (date is predetermined)
            if utils.is_date(date[0]):
                # Multiple Day Reason
                if len(date) == 2:
                    date_from = date[0]
                    date_to = date[1]
                    # only update sheets if reason is to be recorded
                    if inCamp == False:
                        date_from_col = utils.get_index(utils.convert_date_dmy_db(date_from), date_list) + 1
                        date_to_col = utils.get_index(utils.convert_date_dmy_db(date_to), date_list) + 1
                        date_from_A1 = rowcol_to_a1(soldier_row,date_from_col)
                        date_to_A1 = rowcol_to_a1(soldier_row,date_to_col)

                        update_range = "{}:{}".format(date_from_A1,date_to_A1)
                        number_of_col = date_to_col - date_from_col + 1

                        update_dict = {"range": update_range, "values": [["Others"]*number_of_col]}
                        to_batch_update.append(update_dict)
                    db.execute(query, (soldier_id,reason,utils.convert_date_dmy_ymd(date_from),utils.convert_date_dmy_ymd(date_to),str(inCamp),remarks))
                elif date[0] == "PERMANENT":
                    date = date[0]
                    db.execute(query, (soldier_id,reason,date,date,str(inCamp),remarks))
                # Single Day Reason
                else:
                    date = date[0]
                    # only update sheets if reason is to be recorded
                    if inCamp == False:
                        converted_date = utils.convert_date_dmy_db(date)
                        date_col = utils.get_index(converted_date, date_list) + 1
                        to_update_cells.append(Cell(row=soldier_row, col=date_col, value="Others"))
                    db.execute(query, (soldier_id,reason,utils.convert_date_dmy_ymd(date),utils.convert_date_dmy_ymd(date),str(inCamp),remarks))
            # case where date is not inputed (temporary reason)
            else:
                db.execute(query, (soldier_id,reason,"","",str(inCamp),remarks))
            result_msg.append(soldier_name)
    db.commit()
    db.close()
    worksheet.batch_update(to_batch_update)
    if len(to_update_cells) > 0:
        worksheet.update_cells(to_update_cells)
    return result_msg

def update_gsheet_and_db_rs(msg,location):
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    db = sqlite3.connect(db_path)

    name_list = worksheet.col_values(4)
    date_list = worksheet.row_values(2)
    sct_list = worksheet.col_values(6)

    date = datetime.now().strftime("%d%m%y")
    converted_date = utils.convert_date_dmy_db(date)
    date_col = utils.get_index(converted_date, date_list) + 1

    to_update_cells = []
    result_msg = []
    unformatted_msg = utils.unformat_msg(msg, "rs")
    for soldier_info in unformatted_msg:
        name = soldier_info["NAME"].upper()
        remarks = soldier_info["REMARKS"]
        id_4d = soldier_info["4D"]
        try:
            if id_4d != "":
                soldier_row = utils.get_index(id_4d,sct_list) + 1
            else:
                soldier_row = utils.get_name_index(name, name_list) + 1
        except utils.NameConflict as names:
            raise
        except:
            raise NotFound

        soldier_name = name_list[soldier_row-1]
        cursor = db.execute("SELECT SoldierID FROM SoldierInfo WHERE Name = ?", (soldier_name,))
        data = cursor.fetchone()
        soldier_id = data[0]
        if soldier_info["DELETE"]:
            query = '''
            DELETE FROM ReportingSick
            WHERE SoldierID = ?
            AND Location = ?
            '''
            if location == "RSO":
                to_update_cells.append(Cell(row=soldier_row, col=date_col, value=""))
            db.execute(query, (soldier_id,location))
        else:
            query = '''
            INSERT INTO ReportingSick
            (SoldierID,Location,Remarks)
            VALUES
            (?,?,?)
            '''
            if location == "RSO":
                to_update_cells.append(Cell(row=soldier_row, col=date_col, value=location))
            db.execute(query, (soldier_id,location,remarks))
            result_msg.append(soldier_name)
    db.commit()
    db.close()
    if len(to_update_cells) > 0:
        worksheet.update_cells(to_update_cells)
    return result_msg

def update_stayout(msg):
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    db = sqlite3.connect(db_path)

    name_list = worksheet.col_values(4)
    id_list = worksheet.col_values(2)
    stayout_col = 8
    to_update_cells = []

    result_msg = []

    query = "UPDATE SoldierInfo SET StayOut = ? WHERE SoldierID = ?"
    unformatted_msg = utils.unformat_msg(msg, "stayout")
    for soldier_info in unformatted_msg:
        name = soldier_info["NAME"].upper()
        stayout = soldier_info["STAYOUT"]
        soldier_row = utils.get_name_index(name, name_list) + 1
        soldier_name = name_list[soldier_row-1]
        soldier_id = id_list[soldier_row-1]
        if stayout.upper() == "STAYOUT":
            to_update_cells.append(Cell(row=soldier_row,col=stayout_col,value="Yes"))
            db.execute(query, ('True', soldier_id))
        else:
            to_update_cells.append(Cell(row=soldier_row,col=stayout_col,value="No"))
            db.execute(query, ('False', soldier_id))
        result_msg.append(soldier_name)
    db.commit()
    db.close()
    if len(to_update_cells) > 0:
        worksheet.update_cells(to_update_cells)
    return result_msg

def generate_nominal_roll():
    db = sqlite3.connect(db_path)
    cursor = db.execute("SELECT Rank, Name FROM SoldierInfo")
    data = cursor.fetchall()
    msg = ""
    for row in data:
        msg += "{} {}\n".format(row[0],row[1])
    return msg.strip()

def add_days_gsheet(day_to_add):
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    date_row = 2
    day_row = 1
    event_row = 3
    date_record = worksheet.row_values(date_row)
    worksheet.resize(rows=999, cols=len(date_record)+day_to_add+1)
    curr_col = len(date_record)
    curr_date = datetime.strptime(date_record[-1], "%d-%b-%y")
    to_update_cells = []
    for i in range(day_to_add):
        curr_col += 1
        curr_date += timedelta(days=1)
        date = curr_date.strftime("%d-%b-%y")
        day = curr_date.strftime("%a").upper()
        if day == "SAT" or day == "SUN":
            event = "WEEKEND"
        else:
            event = "MOVEMENT"
        to_update_cells.append(Cell(row=day_row,col=curr_col,value=day))
        to_update_cells.append(Cell(row=date_row,col=curr_col,value=date))
        to_update_cells.append(Cell(row=event_row,col=curr_col,value=event))
    if len(to_update_cells) > 0:
            worksheet.update_cells(to_update_cells)

def ord_check_names(msg):
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    name_list = worksheet.col_values(4)
    result_list = []
    for name in msg:
        try:
            soldier_row = utils.get_name_index(name, name_list) + 1
        except utils.NameConflict as names:
            raise
        except:
            raise NotFound
        soldier_name = name_list[soldier_row-1]
        result_list.append(soldier_name)
    return result_list

def ord_confirm_delete_record(names):
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url("sheet_url?usp=sharing")
    worksheet = sh.get_worksheet(0)
    name_list = worksheet.col_values(4)
    rank_list = worksheet.col_values(3)
    rank_names = []
    for name in names:
        soldier_row = utils.get_name_index(name, name_list) + 1
        soldier_rank = rank_list[soldier_row-1]
        soldier_name = name_list[soldier_row-1]
        # worksheet.delete_rows(soldier_row)
        rank_list.append("{} {}".format(soldier_rank,soldier_name))
    return rank_names
