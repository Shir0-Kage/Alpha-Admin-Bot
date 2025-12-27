from datetime import datetime, timedelta
import sqlite3
import os
import pytz
import utils
from config import BOOK_IN_STR_HEADER, BOOK_IN_STR_GROUP, BOOK_IN_STR_GROUP_TROOPER, BOOK_IN_STR_GROUP_STAFF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "alpha.db")

def format_date(date):
    try:
        date_obj = datetime.strptime(date, "%d%m%y")
        new_date = date_obj.strftime("%y%m%d")
        return new_date
    except:
        return date

def get_header(date, in_or_out):
    header = BOOK_IN_STR_HEADER

    time = date.strftime("%H%M")
    date = date.strftime("%d%m%y")

    total_coy,total_comd,total_staff,total_trooper = get_total_strength()
    header = header.format(in_or_out=in_or_out,date=date,time=time,
                           total_coy=total_coy,total_comd=total_comd,
                           total_trooper=total_trooper,total_staff=total_staff)
    return header

def get_total_strength():
    db = sqlite3.connect(db_path)

    query = """SELECT GRP, SUM(CASE InCamp WHEN 'True' THEN 1 ELSE 0 END), Count(SoldierInfo.SoldierID)
    FROM SoldierInfo, Attendance
    WHERE SoldierInfo.SoldierID = Attendance.SoldierID
    GROUP BY GRP
    """
    cursor = db.execute(query)
    data = cursor.fetchall()

    total_coy = "{}/{}".format(sum([i[1] for i in data]),
                               sum([i[2] for i in data]))
    total_comd = "{}/{}".format(sum([i[1] for i in data if i[0] == "Officer" or i[0] == "WOSPEC"]),
                               sum([i[2] for i in data if i[0] == "Officer" or i[0] == "WOSPEC"]))
    total_staff = "{}/{}".format(sum([i[1] for i in data if i[0] == "Support Staff"]),
                               sum([i[2] for i in data if i[0] == "Support Staff"]))
    total_trooper = "{}/{}".format(sum([i[1] for i in data if i[0] == "Enlistees"]),
                               sum([i[2] for i in data if i[0] == "Enlistees"]))

    return total_coy,total_comd,total_staff,total_trooper


def get_absent(group_tag, grps, date):
    absent = ""
    absent_count = 0
    db = sqlite3.connect(db_path)
    date = date.strftime("%y%m%d")

    for grp in grps:
        query = """SELECT SoldierInfo.SoldierID
        FROM Attendance, SoldierInfo
        WHERE Attendance.SoldierID = SoldierInfo.SoldierID
        AND GRP = ?
        AND PLT LIKE ?
        AND InCamp = 'False'
        ORDER BY SCT"""
        cursor = db.execute(query, (grp,group_tag+"%"))
        soldier_ids = [i[0] for i in cursor.fetchall()]

        for soldier_id in soldier_ids:
            query = """SELECT Rank, Name, DateFrom, DateTo, Remarks, SCT
            FROM SoldierInfo, MedicalStatus
            WHERE SoldierInfo.SoldierID = MedicalStatus.SoldierID
            AND ? <= MedicalStatus.DateTo
            AND MedicalStatus = 'MC'
            AND SoldierInfo.SoldierID = ?"""
            cursor = db.execute(query, (date,soldier_id))
            data = cursor.fetchone()
            if data:
                if utils.is4D(data[-1]):
                    absent += "{}. {} {} {} ".format(absent_count+1, data[-1], data[0], data[1])
                else:
                    absent += "{}. {} {} ".format(absent_count+1, data[0], data[1])
                if data[2] == data[3]:
                    absent += "(MC 1D {}".format(format_date(data[2]))
                else:
                    absent += "(MC {} {}-{}".format(utils.format_num_days(data[2], data[3]), format_date(data[2]),format_date(data[3]))
                if data[4]:
                    absent += "({}))\n".format(data[4])
                else:
                    absent += ")\n"
                absent_count += 1
                continue

            query = '''
            SELECT Rank, Name, Remarks, SCT
            FROM SoldierInfo, MedicalAppointment
            WHERE SoldierInfo.SoldierID = MedicalAppointment.SoldierID
            AND MedicalAppointment.Date = ?
            AND SoldierInfo.SoldierID = ?
            '''
            cursor = db.execute(query, (date,soldier_id,))
            data = cursor.fetchone()
            if data:
                if utils.is4D(data[-1]):
                    absent += "{}. {} {} {}".format(absent_count+1, data[-1], data[0], data[1])
                else:
                    absent += "{}. {} {}".format(absent_count+1, data[0], data[1])
                if data[2]:
                    absent += "(MA ({}))\n".format(data[2])
                else:
                    absent += "(MA)\n"
                absent_count += 1
                continue

            query = '''
            SELECT Rank, Name, Country, SCT
            FROM SoldierInfo, Leave
            WHERE SoldierInfo.SoldierID = Leave.SoldierID
            AND CASE WHEN ? <= Leave.DateTo OR ? = Leave.DateTo THEN 1 ELSE 0 END
            AND SoldierInfo.SoldierID = ?
            '''
            leave_date = datetime.strptime(date, "%y%m%d")
            leave_date -= timedelta(days=1)
            leave_date = leave_date.strftime("%y%m%d")
            cursor = db.execute(query, (date,leave_date,soldier_id))
            data = cursor.fetchone()
            if data:
                if utils.is4D(data[-1]):
                    absent += "{}. {} {} {}".format(absent_count+1, data[-1], data[0], data[1])
                else:
                    absent += "{}. {} {}".format(absent_count+1, data[0], data[1])
                if "off" in data[2].lower():
                    absent += "(OFF)\n"
                elif "local" in data[2].lower() or data[2] == "":
                    absent += "(Leave)\n"
                else:
                    absent += "({})\n".format(data[2])
                absent_count += 1
                continue

            query = '''
            SELECT Rank, Name, DutyType, SCT
            FROM SoldierInfo, Duty
            WHERE SoldierInfo.SoldierID = Duty.SoldierID
            AND Duty.Date = ?
            AND SoldierInfo.SoldierID = ?
            '''
            cursor = db.execute(query, (date,soldier_id))
            data = cursor.fetchone()
            if data:
                if utils.is4D(data[-1]):
                    absent += "{}. {} {} {} ({})\n".format(absent_count+1, data[-1], data[0], data[1], data[2])
                else:
                    absent += "{}. {} {} ({})\n".format(absent_count+1, data[0], data[1], data[2])
                absent_count += 1
                continue


            query = '''
            SELECT Rank, Name, CourseName, SCT
            FROM SoldierInfo, OnCourse
            WHERE SoldierInfo.SoldierID = OnCourse.SoldierID
            AND ? <= OnCourse.DateTo
            AND SoldierInfo.SoldierID = ?
            '''
            cursor = db.execute(query, (date,soldier_id))
            data = cursor.fetchone()
            if data:
                if utils.is4D(data[-1]):
                    absent += "{}. {} {} {} ({})\n".format(absent_count+1, data[-1], data[0], data[1], data[2])
                else:
                    absent += "{}. {} {} ({})\n".format(absent_count+1, data[0], data[1], data[2])
                absent_count += 1
                continue

            query = """
            SELECT Rank, Name, Reason, Remarks, SCT
            FROM SoldierInfo, Others
            WHERE SoldierInfo.SoldierID = Others.SoldierID
            AND CASE WHEN ? BETWEEN DateFrom AND DateTo THEN 1 WHEN DateTo = '' THEN 1 WHEN DateTo = 'PERMANENT' THEN 1 ELSE 0 END
            AND SoldierInfo.SoldierID = ?
            """
            cursor = db.execute(query, (date,soldier_id))
            data = cursor.fetchone()
            if data:
                if utils.is4D(data[-1]):
                    absent += "{}. {} {} {} ".format(absent_count+1, data[-1], data[0], data[1])
                else:
                    absent += "{}. {} {} ".format(absent_count+1, data[0], data[1])
                if data[3]:
                    absent += "({} ({}))\n".format(data[2], data[3])
                else:
                    absent += "({})\n".format(data[2])
                absent_count += 1
                continue

            query = """
            SELECT Rank, Name, SCT
            FROM SoldierInfo
            WHERE StayOut = 'True'
            AND SoldierID = ?"""
            cursor = db.execute(query, (soldier_id,))
            data = cursor.fetchone()
            if data:
                if utils.is4D(data[-1]):
                    absent += "{}. {} {} {} (Stay Out)\n".format(absent_count+1, data[-1], data[0], data[1])
                else:
                    absent += "{}. {} {} (Stay Out)\n".format(absent_count+1, data[0], data[1])
                absent_count += 1
                continue

            query = """
            SELECT Rank, Name, SCT
            FROM ReportingSick, SoldierInfo
            WHERE ReportingSick.SoldierID = SoldierInfo.SoldierID
            AND Location = 'RSO'
            AND SoldierInfo.SoldierID = ?"""
            cursor = db.execute(query, (soldier_id,))
            data = cursor.fetchone()
            if data:
                if utils.is4D(data[-1]):
                    absent += "{}. {} {} {} (RSO)\n".format(absent_count+1, data[-1], data[0], data[1])
                else:
                    absent += "{}. {} {} (RSO)\n".format(absent_count+1, data[0], data[1])
                absent_count += 1
                continue

    db.close()
    if absent_count > 0:
        absent += "\n"
    return absent_count, absent

def get_status(group_tag, grps, date):
    db = sqlite3.connect(db_path)
    date = date.strftime("%y%m%d")
    nominalroll = ""
    count = 0

    for grp in grps:
        query = """SELECT Rank, Name, MedicalStatus, DateFrom, DateTo, Remarks, SCT
        FROM SoldierInfo, MedicalStatus
        WHERE SoldierInfo.SoldierID = MedicalStatus.SoldierID
        AND ? <= MedicalStatus.DateTo
        AND MedicalStatus != 'MC'
        AND PLT LIKE ?
        AND GRP = ?
        ORDER BY SCT, SoldierInfo.SoldierID"""
        cursor = db.execute(query, (date,group_tag+"%", grp))
        data = cursor.fetchall()

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
                status += "{} {}, ".format(utils.format_num_days(ele[3],ele[4]),ele[2])
                date = "{}-{}".format(format_date(ele[3]), format_date(ele[4]))
            status = status[:-2] + " {}".format(date)
            status = status.strip()
            # if the same person has multiple statuses but not the same dates
            for ele in statusNot_sameDate:
                status += "; {} {} {}-{}".format(utils.format_num_days(ele[3],ele[4]),ele[2], format_date(ele[3]), format_date(ele[4]))
            nominalroll += status + ")\n"
            count += 1
    db.close()
    return count, nominalroll

def get_group(group_name, group_tag, date):
    group = BOOK_IN_STR_GROUP
    db = sqlite3.connect(db_path)

    query = """SELECT GRP, SUM(CASE InCamp WHEN 'True' THEN 1 ELSE 0 END), Count(SoldierInfo.SoldierID)
    FROM SoldierInfo, Attendance
    WHERE SoldierInfo.SoldierID = Attendance.SoldierID
    AND SoldierInfo.PLT LIKE ?
    GROUP BY GRP"""
    cursor = db.execute(query, (group_tag+"%",))
    data = cursor.fetchall()
    total_group = "{}/{}".format(sum([i[1] for i in data]),
                               sum([i[2] for i in data]))
    total_comd = "{}/{}".format(sum([i[1] for i in data if i[0] == "Officer" or i[0] == "WOSPEC"]),
                               sum([i[2] for i in data if i[0] == "Officer" or i[0] == "WOSPEC"]))
    total_staff = "{}/{}".format(sum([i[1] for i in data if i[0] == "Support Staff"]),
                               sum([i[2] for i in data if i[0] == "Support Staff"]))
    total_trooper = "{}/{}".format(sum([i[1] for i in data if i[0] == "Enlistees"]),
                               sum([i[2] for i in data if i[0] == "Enlistees"]))

    comd_absent_count,comd_absent = get_absent(group_tag, ["Officer","WOSPEC"], date)

    if total_group == "0/0":
        return ""

    if group_tag == "SP":
        group = group.format(group_name=group_name, group_tag="SHARK PL",
                         total_group=total_group,
                         total_comd=total_comd,comd_absent=comd_absent)
    else:
        group = group.format(group_name=group_name, group_tag=group_tag,
                         total_group=total_group,
                         total_comd=total_comd,comd_absent=comd_absent)

    if total_trooper != "0/0":
        trooper = BOOK_IN_STR_GROUP_TROOPER
        trooper_absent_count,trooper_absent = get_absent(group_tag, ["Enlistees"], date)
        group += trooper.format(total_trooper=total_trooper,absent=trooper_absent)

    if total_staff != "0/0":
        staff = BOOK_IN_STR_GROUP_STAFF
        staff_absent_count,staff_absent = get_absent(group_tag, ["Support Staff"], date)
        group += staff.format(total_staff=total_staff,staff_absent=staff_absent)

    return group


def get_bookin_strength(in_or_out):
    tz = pytz.timezone('Asia/Singapore')
    now = datetime.now(tz)
    header = get_header(now, in_or_out)
    groups = {"COY HQ":"Coy HQ",
              "PLATOON 1":"P1",
              "PLATOON 2":"P2",
              "PLATOON 3": "P3",
              "PLATOON 4": "P4",
              "PLATOON 5": "P5",
              "SHARK PL": "SP"}
    body = ""
    for group in groups.keys():
        body += get_group(group, groups[group], now)
    return header + body
