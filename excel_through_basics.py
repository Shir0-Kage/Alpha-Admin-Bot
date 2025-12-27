import sqlite3
import os
from config import SERVICE_ACCOUNT, sheet_url
import utils
from datetime import timedelta
from gspread import Cell

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "alpha.db")

def is4D(check):
    if len(str(check)) == 4 and check.isdigit():
        return True
    return False

def get_repeated(check):
    repeated = []
    checked = []
    for i in check:
        if i in checked:
            repeated.append(i)
        checked.append(i)
    return repeated

def updateRation():
    db = sqlite3.connect(db_path)
    gc = SERVICE_ACCOUNT
    sh = gc.open_by_url(sheet_url)
    worksheet = sh.get_worksheet(0)
    ration_type = worksheet.col_values(9)
    id_list = worksheet.col_values(2)
    print(id_list)
    query = "DELETE FROM RationType"
    db.execute(query)
    # To update when new soldierID is added
    for i, soldier_id in enumerate(id_list):
        if len(soldier_id) == 16:
            ration = ration_type[i]
            query = """INSERT INTO RationType
            (SoldierID, Ration)
            VALUES
            (?, ?)
            """
            db.execute(query, (soldier_id,ration))
    db.commit()
    db.close()
    
# updateRation()
    
def get_absent(plt, date):
    db = sqlite3.connect(db_path)
    date = date.strftime("%y%m%d")
    
    query = """SELECT SoldierInfo.SoldierID
    FROM Attendance, SoldierInfo 
    WHERE Attendance.SoldierID = SoldierInfo.SoldierID
    AND Rank = 'REC'
    AND InCamp = 'False'
    AND PLT LIKE ?"""
    cursor = db.execute(query, (plt,))
    soldier_ids = [i[0] for i in cursor.fetchall()]

    absent_reason = {}
    
    for soldier_id in soldier_ids:
        query = """SELECT SCT
        FROM SoldierInfo, MedicalStatus
        WHERE SoldierInfo.SoldierID = MedicalStatus.SoldierID
        AND ? BETWEEN MedicalStatus.DateFrom AND MedicalStatus.DateTo
        AND SoldierInfo.SoldierID = ?
        AND MedicalStatus = 'MC'
        ORDER BY SCT, SoldierInfo.SoldierID"""
        cursor = db.execute(query, (date,soldier_id))
        data = cursor.fetchone()
        if data:
            absent_reason[data[0]] = "MC"
            continue
    
        query = '''
        SELECT Name, Remarks, SCT
        FROM SoldierInfo, MedicalAppointment
        WHERE SoldierInfo.SoldierID = MedicalAppointment.SoldierID
        AND MedicalAppointment.Date = ?
        AND SoldierInfo.SoldierID = ?
        '''
        cursor = db.execute(query, (date,soldier_id))
        data = cursor.fetchone()
        if data:
            absent_reason[data[0]] = "MA"
            continue

        query = """
        SELECT SCT
        FROM SoldierInfo
        INNER JOIN Others
        ON SoldierInfo.SoldierID = Others.SoldierID
        WHERE CASE WHEN ? BETWEEN DateFrom AND DateTo THEN 1 WHEN DateTo = '' THEN 1 WHEN DateTo = 'PERMANENT' THEN 1 ELSE 0 END
        AND SoldierInfo.SoldierID = ?
        """
        cursor = db.execute(query, (date,soldier_id))
        data = cursor.fetchone()
        if data:
            absent_reason[data[0]] = "OTHERS"
            continue
    db.close()
    return absent_reason

def get_status(plt, date):
    db = sqlite3.connect(db_path)
    date = date.strftime("%y%m%d")
    
    absent_reason = {}
    
    query = """SELECT SCT, MedicalStatus
    FROM SoldierInfo, MedicalStatus
    WHERE SoldierInfo.SoldierID = MedicalStatus.SoldierID
    AND ? BETWEEN MedicalStatus.DateFrom AND MedicalStatus.DateTo
    AND CASE WHEN MedicalStatus = 'LD' THEN 1 WHEN MedicalStatus = 'RIB' THEN 1 ELSE 0 END
    AND PLT LIKE ?
    AND Rank = 'REC'
    ORDER BY SCT, SoldierInfo.SoldierID"""
    cursor = db.execute(query, (date, plt))
    data = cursor.fetchall()
    
    for row in data:
        if row[1].strip().upper() == "LD":
            absent_reason[row[0]] = "LD"
        elif row[1].strip().upper() == "RIB":
            absent_reason[row[0]] = "RIB"
    db.close()
    return absent_reason
    
def get_status_d1(plt, date):
    db = sqlite3.connect(db_path)
    yest = date - timedelta(days=1)
    date = yest.strftime("%y%m%d")
    
    absent_reason = {}
    
    query = """SELECT SCT
    FROM SoldierInfo, MedicalStatus, Attendance
    WHERE SoldierInfo.SoldierID = MedicalStatus.SoldierID
    AND SoldierInfo.SoldierID = Attendance.SoldierID
    AND MedicalStatus = 'MC'
    AND Attendance.InCamp = 'True'
    AND RANK = 'REC'
    AND DateTo = ?
    AND PLT LIKE ?
    ORDER BY SCT
    """
    cursor = db.execute(query, (date, plt))
    data = cursor.fetchall()
    
    for row in data:
        absent_reason[row[0]] = "MC/ LD D1"
    db.close()
    return absent_reason
    
def insert_into_ws(worksheet, dict, date, id_list, date_list, activity_list):
    date = date.strftime("%d/%m/%y")
    to_update = []
    found_today = False
    # loop thru activity list to find today's activity
    for i in range(len(activity_list)):
        # when reach the last date
        if i > len(date_list)-1:
            # if last date is today and loop has not been broken
            if found_today == True:
                current_participating_list = worksheet.col_values(i+1)
                for id_4d in dict.keys():
                    id_row = id_list.index(id_4d)
                    if id_row < len(current_participating_list):
                        if current_participating_list[id_row] != "NA":
                            to_update.append(Cell(row=id_row+1,col=i+1,value=dict[id_4d]))
                    else:
                        to_update.append(Cell(row=id_row+1,col=i+1,value=dict[id_4d]))
        else:
            current_date = date_list[i]
            # if found today's columns
            if current_date == date:
                found_today = True
                current_participating_list = worksheet.col_values(i+1)
                for id_4d in dict.keys():
                    id_row = id_list.index(id_4d)
                    if id_row < len(current_participating_list):
                        if current_participating_list[id_row] != "NA":
                            to_update.append(Cell(row=id_row+1,col=i+1,value=dict[id_4d]))
                    else:
                        to_update.append(Cell(row=id_row+1,col=i+1,value=dict[id_4d]))
            # if already found today column & today has multiple activities
            elif found_today == True and current_date == "":
                current_participating_list = worksheet.col_values(i+1)
                for id_4d in dict.keys():
                    id_row = id_list.index(id_4d)
                    if id_row < len(current_participating_list):
                        if current_participating_list[id_row] != "NA":
                            to_update.append(Cell(row=id_row+1,col=i+1,value=dict[id_4d]))
                    else:
                        to_update.append(Cell(row=id_row+1,col=i+1,value=dict[id_4d]))
            elif found_today == True and current_date != "":
                break
    if len(to_update) > 0:
        worksheet.update_cells(to_update)
    
def update_attendance():
    gc = SERVICE_ACCOUNT
    plt_urls = {}
    today = utils.get_now()
    for plt in plt_urls.keys():
        url = plt_urls[plt]
        sh = gc.open_by_url(url)
        for worksheet in sh.worksheets():
            try:
                # find sheet to insert
                date = today.strftime("%d/%m/%y")
                date_list = worksheet.row_values(4)
                date = date_list.index(date)
            except:
                continue
            else:
                id_list = worksheet.col_values(1)
                activity_list = worksheet.row_values(2)
                absent = get_absent("%"+plt+"%", today)
                status = get_status("%"+plt+"%", today)
                status_d1 = get_status_d1("%"+plt+"%", today)
                if status_d1 != {}:
                    insert_into_ws(worksheet, status_d1, today, id_list, date_list, activity_list)
                if status != {}:
                    insert_into_ws(worksheet, status, today, id_list, date_list, activity_list)
                if absent != {}:
                    insert_into_ws(worksheet, absent, today, id_list, date_list, activity_list)
            

# update_attendance()

