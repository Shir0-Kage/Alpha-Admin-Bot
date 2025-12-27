from datetime import datetime, timedelta
import sqlite3
import os
from config import HEADER_FORMAT, DIVIDER, GROUP_FORMAT, SPECIAL_CASE_FORMAT, TROOPER_FORMAT, SUPPORT_STAFF_FORMAT, SERVICE_ACCOUNT, sheet_url
import pytz
import utils

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "alpha.db")

def get_total_strength():
    db = sqlite3.connect(db_path)
    query = '''
    SELECT GRP, Count(SoldierInfo.SoldierID)
    FROM SoldierInfo, Attendance
    WHERE SoldierInfo.SoldierID = Attendance.SoldierID
    GROUP BY GRP
    '''
    cursor = db.execute(query)
    total_data = cursor.fetchall()
    total_str = sum([row[1] for row in total_data])
    total_officer = sum([row[1] for row in total_data if row[0] == "Officer"])
    total_wose = sum([row[1] for row in total_data if row[0] == "WOSPEC" or row[0] == "Enlistees" or row[0] == "Support Staff"])
    total_sp_staff = sum([row[1] for row in total_data if row[0] == "Support Staff"])
    total_commander = sum([row[1] for row in total_data if row[0] == "Officer" or row[0] == "WOSPEC"])
    total_trooper = sum([row[1] for row in total_data if row[0] == "Enlistees"])

    query = '''
    SELECT GRP, Count(SoldierInfo.SoldierID)
    FROM SoldierInfo, Attendance
    WHERE SoldierInfo.SoldierID = Attendance.SoldierID
    AND Attendance.InCamp = 'True'
    GROUP BY GRP
    '''
    cursor = db.execute(query)
    current_data = cursor.fetchall()
    current_str = sum([row[1] for row in current_data])
    current_officer = sum([row[1] for row in current_data if row[0] == "Officer"])
    current_wose = sum([row[1] for row in current_data if row[0] == "WOSPEC" or row[0] == "Enlistees" or row[0] == "Support Staff"])
    current_sp_staff = sum([row[1] for row in current_data if row[0] == "Support Staff"])
    current_commander = sum([row[1] for row in current_data if row[0] == "Officer" or row[0] == "WOSPEC"])
    current_trooper = sum([row[1] for row in current_data if row[0] == "Enlistees"])

    total_commander_str = "{}/{}".format(current_commander, total_commander)
    total_support_staff_str = "{}/{}".format(current_sp_staff,total_sp_staff)
    grand_total = "{}/{}".format(current_str, total_str)
    total_officer = "{}/{}".format(current_officer, total_officer)
    total_wose = "{}/{}".format(current_wose, total_wose)
    total_trooper_str = "{}/{}".format(current_trooper,total_trooper)

    db.close()
    return total_commander_str,total_support_staff_str,grand_total,total_officer,total_wose,total_trooper_str

def get_nominalroll(data):
    nominalroll = ""
    i = 0
    for row in data:
        if row[0] == "REC":
            nominalroll += "{}. {} {} {} ".format(str(i+1), row[-1], row[0], row[1])
        else:
            nominalroll += "{}. {} {} ".format(str(i+1), row[0], row[1])
        if row[2] == "True":
            nominalroll += "✅\n"
        else:
            nominalroll += "❌\n"
        i += 1
    return nominalroll

def format_date(date):
    try:
        date_obj = datetime.strptime(date, "%d%m%y")
        new_date = date_obj.strftime("%y%m%d")
        return new_date
    except:
        return date

def get_ms_nominalroll(data):
    nominalroll = ""
    count = 0
    while count < len(data):
        row = data[count]
        # add rank & name
        if row[0] == "REC":
            nominalroll += "{}. {} {} {} ".format(str(count+1), row[-1], row[0], row[1])
        else:
            nominalroll += "{}. {} {} ".format(str(count+1), row[0], row[1])
        manyStatus_sameDate = [row]
        statusNot_sameDate = []
        to_pop = []
        for i in range(count+1, len(data)):
            curr = data[i]
            # same soldier with multiple status start and end at same date
            if curr[1] == row[1] and curr[3] == row[3] and curr[4] == row[4]:
                manyStatus_sameDate.append(curr)
                to_pop.append(i)
            # same soldier with multiple status start and end at different dates
            elif curr[1] == row[1]:
                statusNot_sameDate.append(curr)
                to_pop.append(i)
        # remove those that has been added to status to avoid repetition
        for i in to_pop[::-1]:
            data.pop(i)
        # start formating the status
        status = "("
        date = ""
        # if the same person has multiple statuses with same dates
        for ele in manyStatus_sameDate:
            if ele[3] == "PERMANENT":
                status += "; {} {}".format("PERMANENT", ele[2])
            else:
                status += "{} {}, ".format(utils.format_num_days(ele[3],ele[4]),ele[2])
            date = "{}-{}".format(format_date(ele[3]), format_date(ele[4]))
        status = status[:-2] + " {}".format(date)
        status = status.strip()
        # if the same person has multiple statuses but not the same dates
        for ele in statusNot_sameDate:
            if ele[3] == "PERMANENT":
                status += "; {} {}".format("PERMANENT", ele[2])
            else:
                status += "; {} {} {}-{}".format(utils.format_num_days(ele[3],ele[4]),ele[2], format_date(ele[3]), format_date(ele[4]))
        nominalroll += status + ")\n"
        count += 1
    return count, nominalroll

def get_mc_nominalroll(data):
    nominalroll = ""
    count = 0
    data = utils.filter_mc_data(data)
    while count < len(data):
        row = data[count]
        # add rank & name
        if row[0] == "REC":
            nominalroll += "{}. {} {} {} ".format(str(count+1), row[-1], row[0], row[1])
        else:
            nominalroll += "{}. {} {} ".format(str(count+1), row[0], row[1])
        if row[3] == row[4]:
            nominalroll += "1D {}".format(format_date(row[3]))
        else:
            nominalroll += "{} {}-{}".format(utils.format_num_days(row[3],row[4]), format_date(row[3]), format_date(row[4]))
        # if there are remarks
        if row[5]:
            nominalroll += " ({})\n".format(row[5])
        else:
            nominalroll += "\n"
        count += 1
    return count, nominalroll

def get_ma_nominalroll(data):
    nominalroll = ""
    count = 0
    while count < len(data):
        row = data[count]
        # add rank & name
        if row[0] == "REC":
            nominalroll += "{}. {} {} {} ".format(str(count+1), row[-1], row[0], row[1])
        else:
            nominalroll += "{}. {} {} ".format(str(count+1), row[0], row[1])
        nominalroll += "{}".format(format_date(row[2]))
        # if there are remarks
        if row[3] != "":
            nominalroll += " ({})".format(row[3])
        nominalroll += "\n"
        count += 1
    return count, nominalroll

def get_leave_nominalroll(data):
    nominalroll = ""
    count = 0
    while count < len(data):
        row = data[count]
        # add rank & name
        if row[0] == "REC":
            nominalroll += "{}. {} {} {} ".format(str(count+1), row[-1], row[0], row[1])
        else:
            nominalroll += "{}. {} {} ".format(str(count+1), row[0], row[1])
        if row[3] == row[4]:
            nominalroll += "- {}\n".format(row[2])
        else:
            nominalroll += "- {} from {} till {}\n".format(row[2],format_date(row[3]),format_date(row[4]))
        count += 1
    return count, nominalroll

def get_stayout_nominalroll(data):
    nominalroll = ""
    count = 0
    while count < len(data):
        row = data[count]
        # add rank & name
        if row[0] == "REC":
            nominalroll += "{}. {} {} {} ".format(str(count+1), row[-1], row[0], row[1])
        else:
            nominalroll += "{}. {} {} ".format(str(count+1), row[0], row[1])
        nominalroll += "\n"
        count += 1
    return count, nominalroll

def get_course_nominalroll(data):
    nominalroll = ""
    count = 0
    while count < len(data):
        row = data[count]
        # add rank & name
        if row[0] == "REC":
            nominalroll += "{}. {} {} {} ".format(str(count+1), row[-1], row[0], row[1])
        else:
            nominalroll += "{}. {} {} ".format(str(count+1), row[0], row[1])
        if row[3] == row[4]:
            nominalroll += "{} {}\n".format(format_date(row[3]),row[2])
        else:
            nominalroll += "{}-{} {}\n".format(format_date(row[3]),format_date(row[4]),row[2])
        count += 1
    return count, nominalroll

def get_duty_nominalroll(data):
    nominalroll = ""
    count = 0
    while count < len(data):
        row = data[count]
        # add rank & name
        if row[0] == "REC":
            nominalroll += "{}. {} {} {} ".format(str(count+1), row[-1], row[0], row[1])
        else:
            nominalroll += "{}. {} {} ".format(str(count+1), row[0], row[1])
        nominalroll += "- {}\n".format(row[2])
        count += 1
    return count, nominalroll

def get_others_nominalroll(data):
    nominalroll = ""
    count = 0
    while count < len(data):
        row = data[count]
        # add rank & name
        if row[0] == "REC":
            nominalroll += "{}. {} {} {} ".format(str(count+1), row[-1], row[0], row[1])
        else:
            nominalroll += "{}. {} {} ".format(str(count+1), row[0], row[1])
        nominalroll += "- {}".format(row[2])
        # if there is a date inputed
        if utils.is_date(row[3]):
            if row[3] == row[4]:
                nominalroll += " {}".format(format_date(row[3]))
            else:
                nominalroll += " {}-{}".format(format_date(row[3]),format_date(row[4]))
        # if there are remarks
        if row[6] != "":
            nominalroll += " ({})".format(row[6])
        nominalroll += "\n"
        count += 1
    return count, nominalroll

def get_awol_db_cc_ca(date):
    db = sqlite3.connect(db_path)
    query = """
    SELECT Rank, Name, Reason, DateFrom, DateTo, InCamp, Remarks, SCT
    FROM SoldierInfo
	INNER JOIN Others
    ON SoldierInfo.SoldierID = Others.SoldierID
    WHERE CASE WHEN ? BETWEEN DateFrom AND DateTo THEN 1 WHEN DateTo = '' THEN 1 WHEN DateTo = 'PERMANENT' THEN 1 ELSE 0 END
    """
    cursor = db.execute(query, (date,))
    other_data = cursor.fetchall()
    special_case_lst = ("AWOL", "DB", "CC", "CA")
    db.close()
    try:
        counter = [i for i in other_data if i[2].upper() in special_case_lst]
    except:
        return 0
    else:
        return len(counter)

def return_specialcase_nominalroll(case, data):
    if case == "ms":
        count, nominalroll = get_ms_nominalroll(data)
    elif case == "mc":
        count, nominalroll = get_mc_nominalroll(data)
    elif case == "ma":
        count, nominalroll = get_ma_nominalroll(data)
    elif case == "leave":
        count, nominalroll = get_leave_nominalroll(data)
    elif case == "stayout":
        count, nominalroll = get_stayout_nominalroll(data)
    elif case == "course":
        count, nominalroll = get_course_nominalroll(data)
    elif case == "duty":
        count, nominalroll = get_duty_nominalroll(data)
    elif case == "others":
        count, nominalroll = get_others_nominalroll(data)
    return f'{count:02}', nominalroll.strip()

def get_header():
    header = HEADER_FORMAT
    tz = pytz.timezone('Asia/Singapore')
    now = datetime.now(tz)
    today = now.strftime("%d%m%y")
    time = now.strftime("%H%M")
    total_commander_str,total_support_staff_str,grand_total,total_officer,total_wose,total_trooper_str = get_total_strength()
    db_date = now.strftime("%y%m%d")
    dbAwolCcCA = get_awol_db_cc_ca(db_date)
    header = header.format(date=today,time=time,
                  total_commander_str=total_commander_str,
                  total_support_staff_str=total_support_staff_str,
                  total_trooper_str=total_trooper_str,
                  grand_total=grand_total,
                  total_officer=total_officer,
                  total_wose=total_wose,
                  dbAwolCcCA=f"{dbAwolCcCA:02d}")
    return header

def get_groups():
    db = sqlite3.connect(db_path)
    query = "SELECT GroupName, GroupTag FROM GroupSettings"
    cursor = db.execute(query)
    data = cursor.fetchall()
    db.close()
    return data


def get_body():
    db = sqlite3.connect(db_path)
    body = ""
    groups = get_groups()
    for group in groups:
        group_format = GROUP_FORMAT
        group_name = group[0]
        group_tag = group[1]
        query = '''
        SELECT GRP, SUM(CASE InCamp WHEN 'True' THEN 1 ELSE 0 END), Count(SoldierInfo.SoldierID)
        FROM SoldierInfo, Attendance
        WHERE SoldierInfo.SoldierID = Attendance.SoldierID
        AND SoldierInfo.PLT LIKE ?
        GROUP BY GRP
        '''
        cursor = db.execute(query, (group_tag,))
        data = cursor.fetchall()
        # current group
        group_current = sum([row[1] for row in data])
        group_total = sum([row[2] for row in data])
        current_officer = sum([row[1] for row in data if row[0] == "Officer"])
        total_officer = sum([row[2] for row in data if row[0] == "Officer"])
        current_wose = sum([row[1] for row in data if row[0] == "WOSPEC" or row[0] == "Enlistees" or row[0] == "Support Staff"])
        total_wose = sum([row[2] for row in data if row[0] == "WOSPEC" or row[0] == "Enlistees" or row[0] == "Support Staff"])
        current_commander = sum([row[1] for row in data if row[0] == "Officer" or row[0] == "WOSPEC"])
        total_commander = sum([row[2] for row in data if row[0] == "Officer" or row[0] == "WOSPEC"])
        current_trooper = sum([row[1] for row in data if row[0] == "Enlistees"])
        total_trooper = sum([row[2] for row in data if row[0] == "Enlistees"])
        current_sp_staff = sum([row[1] for row in data if row[0] == "Support Staff"])
        total_sp_staff = sum([row[2] for row in data if row[0] == "Support Staff"])

        total_str = "{}/{}".format(group_current, group_total)
        officer_str = "{}/{} ".format(current_officer, total_officer)
        wose_str = "{}/{}".format(current_wose, total_wose)
        commander_str = "{}/{}".format(current_commander,total_commander)
        trooper_str = "{}/{}".format(current_trooper, total_trooper)
        sp_staff_str = "{}/{}".format(current_sp_staff, total_sp_staff)

        query = '''
        SELECT Rank, Name, InCamp, SCT
        FROM SoldierInfo, Attendance
        WHERE SoldierInfo.SoldierID = Attendance.SoldierID
        AND SoldierInfo.PLT LIKE ?
        AND SoldierInfo.GRP = 'Officer'
        '''
        cursor = db.execute(query, (group_tag,))
        officer_data = cursor.fetchall()

        officers = get_nominalroll(officer_data)

        query = '''
        SELECT Rank, Name, InCamp, SCT
        FROM SoldierInfo
        INNER JOIN Attendance
        ON SoldierInfo.SoldierID = Attendance.SoldierID
        WHERE SoldierInfo.PLT LIKE ?
        AND CASE WHEN SoldierInfo.GRP = 'WOSPEC' OR SoldierInfo.GRP = 'Enlistees' OR SoldierInfo.GRP = 'Support Staff' THEN 1 ELSE 0 END
        ORDER BY CASE
        WHEN Rank LIKE 'LTC' THEN 1
        WHEN Rank LIKE 'MAJ' THEN 2
        WHEN Rank LIKE 'CPT'THEN 3
        WHEN Rank LIKE '%WO%' THEN 4
        WHEN Rank LIKE '%LT%' THEN 5
        WHEN Rank LIKE '%SG%' THEN 6
        WHEN Rank LIKE '%CFC%' THEN 7
        WHEN Rank LIKE '%CPL%' THEN 8
        WHEN Rank LIKE '%LCP%' THEN 9
        WHEN Rank LIKE '%PTE%' THEN 10
        WHEN Rank LIKE '%REC%' THEN 11 ELSE 12 END ASC, CASE WHEN SoldierInfo.SCT LIKE '%PS%' THEN 1 WHEN SoldierInfo.SCT LIKE '%SC%' THEN 2 ELSE 3 END ASC, SCT, PLT ASC
        '''
        cursor = db.execute(query, (group_tag,))
        wose_data = cursor.fetchall()

        wose = get_nominalroll(wose_data)
        if total_str == "0/0":
            continue
        body += group_format.format(group_name=group_name,
                    total_str=total_str,
                    officer_str=officer_str,
                    officers=officers,
                    wose_str=wose_str,
                    wose=wose,
                    commander_str=commander_str)
        if int(total_trooper) > 0:
            body += TROOPER_FORMAT.format(trooper_str) + "\n"
        if int(total_sp_staff) > 0:
            body += SUPPORT_STAFF_FORMAT.format(sp_staff_str) + "\n"
        body += "\n" + DIVIDER
    db.close()
    return body

def get_special_cases():
    tz = pytz.timezone('Asia/Singapore')
    db = sqlite3.connect(db_path)
    now = datetime.now(tz)
    date = now.strftime("%y%m%d")

    special_case = SPECIAL_CASE_FORMAT

    query = '''
    SELECT Rank, Name, MedicalStatus, DateFrom, DateTo, Remarks, GRP, SCT
    FROM SoldierInfo, MedicalStatus
    WHERE SoldierInfo.SoldierID = MedicalStatus.SoldierID
    AND ? <= MedicalStatus.DateTo
    AND MedicalStatus != 'MC'
    ORDER BY GRP, SoldierInfo.SoldierID
    '''
    cursor = db.execute(query, (date,))
    ms_data = cursor.fetchall()

    query = '''
    SELECT Rank, Name, MedicalStatus, DateFrom, DateTo, Remarks, SCT
    FROM SoldierInfo, MedicalStatus
    WHERE SoldierInfo.SoldierID = MedicalStatus.SoldierID
    AND ? <= MedicalStatus.DateTo
    AND MedicalStatus = 'MC'
    '''
    cursor = db.execute(query, (date,))
    mc_data = cursor.fetchall()

    query = '''
    SELECT Rank, Name, Date, Remarks, SCT
    FROM SoldierInfo, MedicalAppointment
    WHERE SoldierInfo.SoldierID = MedicalAppointment.SoldierID
    AND MedicalAppointment.Date = ?
    '''
    cursor = db.execute(query, (date,))
    ma_data = cursor.fetchall()

    query = '''
    SELECT Rank, Name, Country, DateFrom, DateTo, Remarks, SCT
    FROM SoldierInfo, Leave
    WHERE SoldierInfo.SoldierID = Leave.SoldierID
    AND ? BETWEEN Leave.DateFrom AND Leave.DateTo
    '''
    cursor = db.execute(query, (date,))
    leave_data = cursor.fetchall()

    query = '''
    SELECT Rank, Name, DutyType, Date, SCT
    FROM SoldierInfo, Duty
    WHERE SoldierInfo.SoldierID = Duty.SoldierID
    AND Duty.Date = ?
    '''
    cursor = db.execute(query, (date,))
    duty_data = cursor.fetchall()

    query = '''
    SELECT Rank, Name, CourseName, DateFrom, DateTo, SCT
    FROM SoldierInfo, OnCourse
    WHERE SoldierInfo.SoldierID = OnCourse.SoldierID
    AND ? BETWEEN OnCourse.DateFrom AND OnCourse.DateTo
    '''
    cursor = db.execute(query, (date,))
    course_data = cursor.fetchall()

    query = """
    SELECT Rank, Name, Reason, DateFrom, DateTo, InCamp, Remarks, SCT
    FROM SoldierInfo
	INNER JOIN Others
    ON SoldierInfo.SoldierID = Others.SoldierID
    WHERE CASE WHEN ? BETWEEN DateFrom AND DateTo THEN 1 WHEN DateTo = '' THEN 1 WHEN DateTo = 'PERMANENT' THEN 1 ELSE 0 END
    """
    cursor = db.execute(query, (date,))
    other_data = cursor.fetchall()

    query = """
    SELECT Rank, Name, SCT
    FROM ReportingSick, SoldierInfo
    WHERE ReportingSick.SoldierID = SoldierInfo.SoldierID
    AND Location = 'RSO'
    """
    cursor = db.execute(query)
    rso_data = cursor.fetchall()

    other_data.extend([(i[0], i[1], "RSO", "", "", "","", i[2]) for i in rso_data])

    query = """
    SELECT Rank, Name, SCT
    FROM SoldierInfo
    WHERE StayOut = 'True'
    """
    cursor = db.execute(query)
    stayout_data = cursor.fetchall()

    status_str, status = return_specialcase_nominalroll("ms", ms_data)
    mc_str, mc = return_specialcase_nominalroll("mc", mc_data)
    ma_str, ma = return_specialcase_nominalroll("ma", ma_data)
    leave_str, leave = return_specialcase_nominalroll("leave", leave_data)
    oncourse_str, oncourse = return_specialcase_nominalroll("course", course_data)
    duty_str, duty = return_specialcase_nominalroll("duty", duty_data)
    others_str, others = return_specialcase_nominalroll("others", other_data)
    stayout_str, stayout = return_specialcase_nominalroll("stayout", stayout_data)

    special_case = special_case.format(status_str=status_str,status=status,
                        mc_str=mc_str,mc=mc,
                        ma_str=ma_str,ma=ma,
                        leave_str=leave_str,leave=leave,
                        stayout_str=stayout_str,stayout=stayout,
                        oncourse_str=oncourse_str,oncourse=oncourse,
                        duty_str=duty_str,duty=duty,
                        others_str=others_str,others=others
                        )
    return special_case

def get_paradestate():
    paradestate = ""
    header = get_header()
    paradestate += header + "\n" + DIVIDER
    body = get_body()
    paradestate += body + "\n"
    special_case = get_special_cases()
    paradestate += special_case
    return paradestate

##################### EXTRA TRACKER GETTERS #######################
def get_status_history(msg):
    status_hist = ""
    if utils.is4D(msg):
        db = sqlite3.connect(db_path)
        query = "SELECT SoldierID, Rank, Name FROM SoldierInfo WHERE SCT = ?"
        data = db.execute(query, (msg,)).fetchone()
        if data:
            soldier_id = data[0]
            status_hist += "{} {} {}\n".format(msg, data[1], data[2])
            query = """SELECT MedicalStatus, DateFrom, DateTo, Remarks
            FROM MedicalStatus
            WHERE SoldierID = ?
            """
            cursor = db.execute(query, (soldier_id,))
            data = cursor.fetchall()
            for row in data:
                status_hist += "{} {}".format(utils.format_num_days(row[1], row[2]), row[0])
                if row[1] == row[2]:
                    status_hist += " ({})".format(format_date(row[1]))
                else:
                    status_hist += " ({}-{})".format(format_date(row[1]), format_date(row[2]))
                if row[3] == "":
                    status_hist += "\n"
                else:
                    status_hist += "({})\n".format(row[3])
        else:
            db.close()
            raise Exception
    else:
        gc = SERVICE_ACCOUNT
        sh = gc.open_by_url(sheet_url)
        worksheet = sh.get_worksheet(0)
        name_list = worksheet.col_values(4)
        soldier_name = name_list[utils.get_name_index(msg, name_list)]

        db = sqlite3.connect(db_path)
        query = "SELECT SoldierID, Rank, Name FROM SoldierInfo WHERE Name = ?"
        data = db.execute(query, (soldier_name,)).fetchone()
        if data:
            soldier_id = data[0]
            status_hist += "{} {}\n".format(data[1], data[2])
            query = """SELECT MedicalStatus, DateFrom, DateTo, Remarks
            FROM MedicalStatus
            WHERE SoldierID = ?
            ORDER BY DateFrom
            """
            cursor = db.execute(query, (soldier_id,))
            data = cursor.fetchall()
            for row in data:
                status_hist += "{} {}".format(utils.format_num_days(row[1], row[2]), row[0])
                if row[1] == row[2]:
                    status_hist += " ({})".format(format_date(row[1]))
                else:
                    status_hist += " ({}-{})".format(format_date(row[1]), format_date(row[2]))
                if row[3] == "":
                    status_hist += "\n"
                else:
                    status_hist += "({})\n".format(row[3])
        else:
            raise Exception
    db.close()
    return status_hist.strip()
