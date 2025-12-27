import os
from telebot import types
from paradestate_func import get_paradestate, get_status_history
from telegrambot import bot, CHAT_ID
import gsheet_db_func
from utils import get_stayout, get_now, reformat_mass_msg, unlock_db, detect_error, unformat_msg, is_date, NameConflict, DateError
import excel_through_basics
from datetime import datetime, timedelta
import pytz
import time
import sqlite3
import random
import book_in_str
import re

INLINE_MSG = ""

@bot.message_handler(commands=['status_history','statushistory'])
def statusHistory(message):
    sent_msg = bot.reply_to(message, "Whose status history would you like to view")
    bot.register_next_step_handler(sent_msg, status_history_handler, sent_msg)

def status_history_handler(message, recur_sent_msg):
    if message.message_thread_id == recur_sent_msg.message_thread_id:
        try:
            name_list = message.text.strip().split("\n")
            status_hist = ""
            for name in name_list:
                status_hist += get_status_history(name) + "\n\n"
        except NameConflict as e:
            markup = types.InlineKeyboardMarkup(row_width=1)
            original_name, names = e.args
            for correct_name in names:
                # SH for status history (callback data size cannot exceed 64 bit)
                markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join(("SH",correct_name))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Conflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
        except:
            unlock_db()
            bot.reply_to(message, "Please enter the correct Rank Name or 4D")
        else:
            sent_msg = bot.reply_to(message, text=status_hist)
    else:
        sent_msg = bot.reply_to(message, text="Status History Active in another chat/topic.")
        bot.register_next_step_handler(message, status_history_handler, recur_sent_msg)


@bot.message_handler(commands=['paradestate', 'parade_state'])
def reply_paradestate(message):
    tz = pytz.timezone("Asia/Singapore")
    date = datetime.now(tz)
    gsheet_db_func.update_attendance_am(date)
    paradestate = get_paradestate()
    if len(paradestate) > 4095:
        for x in range(0, len(paradestate), 4095):
            bot.reply_to(message, text=paradestate[x:x+4095])
    else:
        bot.reply_to(message, text=paradestate)

@bot.message_handler(commands=['bookin_strength', "book_in_strength", "bookin_str", "book_in_str"])
def reply_bookin_strength(message):
    tz = pytz.timezone("Asia/Singapore")
    date = datetime.now(tz)
    gsheet_db_func.update_attendance_pm(date)
    book_in_strength = book_in_str.get_bookin_strength("In")
    if len(book_in_strength) > 4095:
        for x in range(0, len(book_in_strength), 4095):
            bot.reply_to(message, text=book_in_strength[x:x+4095])
    else:
        bot.reply_to(message, text=book_in_strength)

@bot.message_handler(commands=['bookout_strength', "book_out_strength", "bookout_str", "book_out_str"])
def reply_bookout_strength(message):
    tz = pytz.timezone("Asia/Singapore")
    date = datetime.now(tz)
    gsheet_db_func.update_recruits_attendance_am(date)
    book_in_strength = book_in_str.get_bookin_strength("Out")
    if len(book_in_strength) > 4095:
        for x in range(0, len(book_in_strength), 4095):
            bot.reply_to(message, text=book_in_strength[x:x+4095])
    else:
        bot.reply_to(message, text=book_in_strength)

# @bot.message_handler(commands=['bookin_tripline', "book_in_tripline"])
# def reply_bookin_tripline(message):
#     tripline_msg = tripline.get_bookin_msg()
#     bot.reply_to(message, text=tripline_msg)

@bot.message_handler(commands=['LPparadestate','LP_paradestate', 'lp_paradestate', 'lpparadestate','Lpparadestate', 'Lp_paradestate'])
def reply_LPparadestate(message):
    tz = pytz.timezone("Asia/Singapore")
    date = datetime.now(tz)
    gsheet_db_func.update_attendance_pm(date)
    paradestate = get_paradestate()
    if len(paradestate) > 4095:
        for x in range(0, len(paradestate), 4095):
            bot.reply_to(message, text=paradestate[x:x+4095])
    else:
        bot.reply_to(message, text=paradestate)

@bot.message_handler(commands=['update_info'])
def updateInfo(message):
    gsheet_db_func.update_db_info_from_gsheet()
    bot.reply_to(message, "Updated Successfully!")

@bot.message_handler(commands=['update_ration'])
def updateRations(message):
    excel_through_basics.updateRation()
    bot.reply_to(message, "Updated Successfully!")

# @bot.message_handler(commands=['ribRations','rib_rations', 'RIB_rations'])
# def getRibRations(message):
#     rations = recruit_paradestate.getRIB_ration()
#     if rations:
#         bot.reply_to(message, rations)
#     else:
#         bot.reply_to(message, "No Ribs")

# @bot.message_handler(commands=['rsiRations','rsi_rations'])
# def getRsiRations(message):
#     rations = recruit_paradestate.getRSI_ration()
#     if rations:
#         bot.reply_to(message, rations)
#     else:
#         bot.reply_to(message, "No RSIs")

# @bot.message_handler(commands=['returning_from_MC','returning_from_mc',"returning_from_Mc"])
# def getReturningFromMC(message):
#     tz = pytz.timezone("Asia/Singapore")
#     today = datetime.now(tz)
#     returning_from_mc = recruit_paradestate.get_returning_from_MC(today)
#     if returning_from_mc:
#         bot.reply_to(message, returning_from_mc)
#     else:
#         bot.reply_to(message, "No One back from MC")

# @bot.message_handler(commands=['get_skivers'])
# def get_skivers(message):
#     sent_msg = bot.reply_to(message, "Which day conduct would you like to keng?")
#     bot.register_next_step_handler(sent_msg, skiver_getter)

# def skiver_getter(message):
#     try:
#         date = datetime.strptime(message.text, "%d%m%y")
#     except:
#         sent_msg = bot.reply_to(message, "Please enter date in the ddmmyy format")
#         bot.register_next_step_handler(sent_msg, skiver_getter)
#     else:
#         skivers = recruit_paradestate.get_non_participatnts(date)
#         bot.reply_to(message, skivers)

@bot.message_handler(commands=['update_duty'])
def update_duty(message):
    gsheet_db_func.update_db_from_gsheet_duty()
    gsheet_db_func.update_db_from_gsheet_trooper_duty()
    bot.reply_to(message, "Updated Successfully!")

# @bot.message_handler(commands=['paradestate_history'])
# def reply_paradestate(message):
#     sent_msg = bot.reply_to(message, "Which day's paradestate would you like to view")
#     bot.register_next_step_handler(sent_msg, paradestate_history_handler)

# def paradestate_history_handler(message):
#     try:
#         date = datetime.strptime(message.text, "%d%m%y")
#     except:
#         bot.reply_to(message, "Please enter date in the ddmmyy format")
#     else:
#         gsheet_db_func.update_attendance_am(date)
#         gsheet_db_func.update_recruits_attendance_am(date)
#         paradestate = recruit_paradestate.getCoyParadestate(date)
#         if len(paradestate) > 4095:
#             for x in range(0, len(paradestate), 4095):
#                 bot.reply_to(message, text=paradestate[x:x+4095])
#         else:
#             bot.reply_to(message, text=paradestate)

@bot.message_handler(commands=['add_days'])
def add_days(message):
    sent_msg = bot.reply_to(message, "How many days to add?")
    bot.register_next_step_handler(sent_msg, add_days_handler)

def add_days_handler(message):
    try:
        gsheet_db_func.add_days_gsheet(int(message.text.strip()))
    except:
        sent_msg = bot.reply_to(message, "Please enter a number.")
        bot.register_next_step_handler(sent_msg, add_days_handler)
    else:
        bot.reply_to(message, "Days added successfully!")


@bot.message_handler(commands=['help'])
def help(message):
    help_msg = """<<ALPHA ADMIN BOT MANUAL>>
[Paradestate Commands]
/paradestate : generate current parade state message
/LPparadestate : update and generate paradestate for last parade (bookouts, stayouts etc)
/bookin_str: get book-in strength

[Updating Paradestate]
- /nominalRoll : generates a nominal roll of names
- /format: get formatting examples

[Useful Commands]
- /ribRations: get all rib 4D, name and ration types
- /status_history: get all status history of a person"""
    bot.reply_to(message, help_msg)

@bot.message_handler(commands=['patch_notes'])
def reply_paradestate(message):
    patch_msg = """Alpha Admin Bot v1.5
-New Features-
1. new update syntax: 'UPDATE', used to update remarks for an existing record, don't need to delete then update just for remarks
i.e. 1234 MC does not have remarks/have wrong remarks
|
STATUS:
UPDATE 1234 230324-240324 (borderline IQ)
|

2. new feature! Can update by just inputing the number of days
i.e.
|
STATUS:
1234 2D MC (retarded)
|
Note: the start date is defaulted to today, only works if status starts today
Also works for updating others/courses/leaves etc.

3. bot now recognises what kind of error the message have & replies with the error
----------------------------------
-Updates-
- duties are now updated daily at 0000 to reduce error from last min changes
- /status_history dont need to keep /status_history for consecutive use, can straight away enter another 4d and get their status history
(will not work if another msg in another topic interupts this chain)
- Note: after /status_history it will wait for a reply so other commands will not work
- Removed Herobrine
- OTHERS: NotInCamp/InCamp is now case insensitive!
- MC Day 1 only get those who are coming back to camp, ignoring MA/extended MCs
"""
    bot.reply_to(message, patch_msg)

@bot.message_handler(commands=['format','format_example','example'])
def reply_paradestate(message):
    patch_msg = """*Message Formats*
STATUS:
Name Date Status (Remarks)

MA:
Name Date (Remarks)

LEAVE:
Name Date Country (Remarks)

COURSE:
Name Date CourseName (Remarks)

RSI/RSO:
Name (Remarks)

OTHERS:
4D InCamp/NotInCamp Date Reason (Remarks)
Note: For Others Date is optional but if not provided, will be permanent until deleted
"""
    bot.reply_to(message, patch_msg, parse_mode="Markdown")

@bot.message_handler(commands=['stayout'])
def update_stayout(message):
    today = get_now()
    gsheet_db_func.update_attendance_pm(today)
    reply_text = get_stayout()
    if reply_text == "":
        reply_text = "Nobody is staying out"
    else:
        reply_text = "Stay Out Personnels:\n" + reply_text

    markup = types.InlineKeyboardMarkup(row_width=1)
    sent_msg = bot.reply_to(message, reply_text, reply_markup=markup)
    bot.register_next_step_handler(sent_msg, stayout_result_handler)


@bot.message_handler(commands=['update_attendance'])
def update_db(message):
    excel_through_basics.update_attendance()
    bot.reply_to(message, "Updated Successfully!")

def result_handler(message, table):
    msg = message.text
    markup = types.InlineKeyboardMarkup(row_width=1)
    update_msg, is_mass_update = parse_update_message(msg)
    if is_mass_update == True:
        update_msg = reformat_mass_msg(update_msg)
    if table == "duty":
        try:
            result = gsheet_db_func.update_gsheet_and_db_duty(update_msg)
        except sqlite3.OperationalError:
            unlock_db()
            gsheet_db_func.update_gsheet_and_db_duty(update_msg)
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Updated Duty Successfully!")
        except sqlite3.IntegrityError:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="This record already exist.")
            unlock_db()
        except gsheet_db_func.NotFound:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Cannot find 4D/Name.")
            unlock_db()
        except NameConflict as e:
            original_name, names = e.args
            for correct_name in names:
                markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join((table,correct_name))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Error updating: \n"{}"\nConflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
        except ValueError:
            reply_msg = "Please Enter the valid format: 4D Date DutyType (Remarks)"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
        except DateError:
            reply_msg = "Please Enter the Date Correctly"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
        except:
            error = None
            msg_lst = unformat_msg(update_msg, "duty")
            for msg_dict in msg_lst:
                error = detect_error(msg_dict)
            if error:
                reply_msg = "Please Enter the valid format: 4D Date DutyType (Remarks)"
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=error)
            else:
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="uh oh seems like the code fked up again bozo 🦧")
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="I give u 5 mins to fix ur code")
            unlock_db()
        else:
            reply_msg = "Updated Duty Successfully!"
            for name in result:
                reply_msg += name + "\n"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
    elif table == "leave":
        try:
            result = gsheet_db_func.update_gsheet_and_db_leaves(update_msg)
        except sqlite3.OperationalError:
            unlock_db()
            gsheet_db_func.update_gsheet_and_db_leaves(update_msg)
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Updated Leave Successfully!")
        except sqlite3.IntegrityError:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="This record already exist.")
            unlock_db()
        except gsheet_db_func.NotFound:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Cannot find 4D/Name.")
            unlock_db()
        except NameConflict as e:
            original_name, names = e.args
            for correct_name in names:
                markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join((table,correct_name))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Error updating: \n"{}"\nConflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
        except DateError:
            reply_msg = "Please Enter the Date Correctly"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
        except:
            error = None
            msg_lst = unformat_msg(update_msg, table)
            for msg_dict in msg_lst:
                error = detect_error(msg_dict)
            if error:
                reply_msg = "Please Enter the valid format: 4D Date Local/Country (Remarks)"
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=error)
            else:
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="uh oh seems like the code fked up again bozo 🦧")
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="I give u 5 mins to fix ur code")
            unlock_db()
        else:
            reply_msg = "Updated Leave Successfully!"
            for name in result:
                reply_msg += name + "\n"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
    elif table == "ma":
        try:
            result = gsheet_db_func.update_gsheet_and_db_ma(update_msg)
        except sqlite3.OperationalError:
            unlock_db()
            gsheet_db_func.update_gsheet_and_db_ma(update_msg)
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Updated MA Successfully!")
        except sqlite3.IntegrityError:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="This record already exist.")
            unlock_db()
        except gsheet_db_func.NotFound:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Cannot find 4D/Name.")
            unlock_db()
        except NameConflict as e:
            original_name, names = e.args
            for correct_name in names:
                markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join((table,correct_name))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Error updating: \n"{}"\nConflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
        except DateError:
            reply_msg = "Please Enter the Date Correctly"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
        except:
            error = None
            msg_lst = unformat_msg(update_msg, table)
            for msg_dict in msg_lst:
                error = detect_error(msg_dict)
            if error:
                reply_msg = "Please Enter the valid format: 4D Date (Remarks)"
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=error)
            else:
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="uh oh seems like the code fked up again bozo 🦧")
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="I give u 5 mins to fix ur code")
            unlock_db()
        else:
            reply_msg = "Updated MA Successfully!\n"
            for name in result:
                reply_msg += name + "\n"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
    elif table == "ms":
        try:
            result = gsheet_db_func.update_gsheet_and_db_ms(update_msg)
        except sqlite3.OperationalError:
            unlock_db()
            gsheet_db_func.update_gsheet_and_db_ms(update_msg)
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Updated Status Successfully!")
        except sqlite3.IntegrityError:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="This record already exist.")
            unlock_db()
        except gsheet_db_func.NotFound:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Cannot find 4D/Name.")
            unlock_db()
        except gsheet_db_func.NoDetail:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Status not inputed/Wrong Format.")
        except NameConflict as e:
            original_name, names = e.args
            for correct_name in names:
                markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join((table,correct_name))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Error updating: \n"{}"\nConflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
        except DateError:
            reply_msg = "Please Enter the Date Correctly"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
        except:
            error = None
            msg_lst = unformat_msg(update_msg, table)
            for msg_dict in msg_lst:
                error = detect_error(msg_dict)
            if error:
                reply_msg = "Please Enter the valid format: 4D Date Status (Remarks)"
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=error)
            else:
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="uh oh seems like the code fked up again bozo 🦧")
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="I give u 5 mins to fix ur code")
            unlock_db()
        else:
            reply_msg = "Updated Status Successfully!\n"
            for row in result:
                soldier_name = row[0]
                num_days = row[1]
                status = row[2]
                date_from = row[3]
                date_to = row[4]
                reply_msg += "{} {} {} {}-{}\n".format(soldier_name,num_days,status,date_from,date_to)
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg.strip())
    elif table == "course":
        try:
            result = gsheet_db_func.update_gsheet_and_db_course(update_msg)
        except sqlite3.OperationalError:
            unlock_db()
            gsheet_db_func.update_gsheet_and_db_course(update_msg)
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Updated Course Successfully!")
        except sqlite3.IntegrityError:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="This record already exist.")
            unlock_db()
        except gsheet_db_func.NotFound:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Cannot find 4D/Name.")
            unlock_db()
        except NameConflict as e:
            original_name, names = e.args
            for correct_name in names:
                markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join((table,correct_name))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Error updating: \n"{}"\nConflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
        except DateError:
            reply_msg = "Please Enter the Date Correctly"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
        except:
            error = None
            msg_lst = unformat_msg(update_msg, table)
            for msg_dict in msg_lst:
                error = detect_error(msg_dict)
            if error:
                reply_msg = "Please Enter the valid format: 4D Date CourseName (Remarks)"
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=error)
            else:
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="uh oh seems like the code fked up again bozo 🦧")
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="I give u 5 mins to fix ur code")
            unlock_db()
        else:
            reply_msg = "Updated Course Successfully!\n"
            for name in result:
                reply_msg += name + "\n"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
    elif table == "rsi":
        try:
            result = gsheet_db_func.update_gsheet_and_db_rs(update_msg,"RSI")
        except sqlite3.OperationalError:
            unlock_db()
            gsheet_db_func.update_gsheet_and_db_rs(update_msg,"RSI")
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Updated RSI Successfully!")
        except sqlite3.IntegrityError:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text= "This record already exist.")
            unlock_db()
        except gsheet_db_func.NotFound:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text= "Cannot find 4D/Name.")
            unlock_db()
        except NameConflict as e:
            original_name, names = e.args
            for correct_name in names:
                markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join((table,correct_name))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Error updating: \n"{}"\nConflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
        except DateError:
            reply_msg = "Please Enter the Date Correctly"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
        except:
            error = None
            msg_lst = unformat_msg(update_msg, table)
            for msg_dict in msg_lst:
                error = detect_error(msg_dict)
            if error:
                reply_msg = """Please Enter the valid format: 4D (Remarks)"""
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=error)
            else:
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="uh oh seems like the code fked up again bozo 🦧")
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="I give u 5 mins to fix ur code")
            unlock_db()
        else:
            reply_msg = "Updated RSI Successfully!\n"
            for soldier_name in result:
                reply_msg += "{}\n".format(soldier_name)
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg.strip())
    elif table == "rso":
        try:
            result = gsheet_db_func.update_gsheet_and_db_rs(update_msg,"RSO")
        except sqlite3.OperationalError:
            unlock_db()
            gsheet_db_func.update_gsheet_and_db_rs(update_msg,"RSO")
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Updated RSO Successfully!")
        except sqlite3.IntegrityError:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="This record already exist.")
            unlock_db()
        except gsheet_db_func.NotFound:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Cannot find 4D/Name.")
            unlock_db()
        except NameConflict as e:
            original_name, names = e.args
            for correct_name in names:
                markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join((table,correct_name))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Error updating: \n"{}"\nConflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
        except DateError:
            reply_msg = "Please Enter the Date Correctly"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
        except:
            error = None
            msg_lst = unformat_msg(update_msg, table)
            for msg_dict in msg_lst:
                error = detect_error(msg_dict)
            if error:
                reply_msg = """Please Enter the valid format: 4D (Remarks)"""
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=error)
            else:
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="uh oh seems like the code fked up again bozo 🦧")
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="I give u 5 mins to fix ur code")
            unlock_db()
        else:
            reply_msg = "Updated RSO Successfully!\n"
            for soldier_name in result:
                reply_msg += "{}\n".format(soldier_name)
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg.strip())
    elif table == "ord":
        try:
            names = gsheet_db_func.ord_check_names(update_msg)
        except NameConflict as e:
            original_name, names = e.args
            for correct_name in names:
                markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join((table,correct_name))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Error updating: \n"{}"\nConflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
        except:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Name Not Found')
        else:
            markup.add(types.InlineKeyboardButton("YES", callback_data="/,/".join(("CONFRIM_ORD","Y"))))
            markup.add(types.InlineKeyboardButton("Cancel Last", callback_data="/,/".join(("CONFRIM_ORD","N"))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Are you sure you want to ORD the following:\n{}'.format("\n".join(names)), reply_markup=markup)
    else:
        try:
            result = gsheet_db_func.update_gsheet_and_db_others(update_msg)
        except sqlite3.OperationalError:
            unlock_db()
            gsheet_db_func.update_gsheet_and_db_others(update_msg)
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Updated Others Successfully!")
        except sqlite3.IntegrityError:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="This record already exist.")
            unlock_db()
        except gsheet_db_func.NotFound:
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="Cannot find 4D/Name.")
            unlock_db()
        except NameConflict as e:
            original_name, names = e.args
            for correct_name in names:
                markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join((table,correct_name))))
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Error updating: \n"{}"\nConflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
        except DateError:
            reply_msg = "Please Enter the Date Correctly"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
        except:
            error = None
            msg_lst = unformat_msg(update_msg, table)
            for msg_dict in msg_lst:
                error = detect_error(msg_dict)
            if error:
                reply_msg = """Please Enter the valid format: 4D InCamp/NotInCamp Date Reason (Remarks)"""
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=error)
            else:
                bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="uh oh seems like the code fked up again bozo 🦧")
                msg = bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="I give u 5 mins to fix ur code")
            unlock_db()
        else:
            reply_msg = "Updated Others Successfully!\n"
            for name in result:
                reply_msg += name + "\n"
            bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text=reply_msg)

@bot.callback_query_handler(func=lambda call:True)
def update_handler(callback):
    """callback_data=(table,correct_name)"""
    if callback.message:
        msg = callback.message
        bot.edit_message_reply_markup(chat_id=msg.chat.id, message_id=msg.message_id)
        table, correct_name = callback.data.split("/,/")
        if table == "SH":
            status_hist = get_status_history(correct_name)
            bot.send_message(chat_id=msg.chat.id,message_thread_id=msg.message_thread_id,text=status_hist)
        elif table == "SO":
            msg_text = msg.text
            message = msg_text.split('Error updating: \n"')[1].split('"\n')[0]
            original_name = msg_text.split('Conflicting name: "')[1].split('",')[0]
            message = re.sub(original_name, correct_name, message, flags=re.IGNORECASE)
            msg.text = message
            stayout_result_handler(msg)
        elif table == "CONFRIM_ORD":
            if correct_name == "Y":
                msg_text = msg.text
                names = msg_text.split(':\n')[1].split('\n')
                rank_names = gsheet_db_func.ord_confirm_delete_record(names)
                bot.send_message(chat_id=msg.chat.id,message_thread_id=msg.message_thread_id,text="OWADIOOOOO!!!!! THANK YOU FOR YOUR FUCKING SERVICE:\n{}".format("\n".join(rank_names)))
                bot.send_sticker(chat_id=msg.chat.id,message_thread_id=msg.message_thread_id,sticker="CAACAgUAAxkBAAExIodnlZZOzs56tSuKr1E9F0VdL5XDZAAC-QQAAhR4wVbXOPRsgklAcjYE")
                time.sleep(5)
                bot.send_sticker(chat_id=msg.chat.id,message_thread_id=msg.message_thread_id,sticker="CAACAgUAAxkBAAExIolnlZZRS2SvOtWEu57eUobYZHmxowACMwUAAsoyyVbzRAorKaVZwzYE")
                gsheet_db_func.update_db_info_from_gsheet()
            else:
                bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.message_id,text="ORD Revoked, Sign on 5 more years")
        else:
            msg_text = msg.text
            message = msg_text.split('Error updating: \n"')[1].split('"\n')[0]
            original_name = msg_text.split('Conflicting name: "')[1].split('",')[0]
            message = re.sub(original_name, correct_name, message, flags=re.IGNORECASE)
            msg.text = message
            result_handler(msg,table)


def stayout_result_handler(message):
    msg = message.text
    update_msg = msg.strip().split("\n")
    try:
        gsheet_db_func.update_stayout(update_msg)
    except NameConflict as e:
        markup = types.InlineKeyboardMarkup(row_width=1)
        original_name, names = e.args
        for correct_name in names:
            # SH for status history (callback data size cannot exceed 64 bit)
            markup.add(types.InlineKeyboardButton(correct_name, callback_data="/,/".join(("SO",correct_name))))
        bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text='Conflicting name: "{}", please choose the correct one.'.format(message.text,original_name), reply_markup=markup)
    bot.reply_to(message, "Updated Successfully!")

@bot.message_handler(commands=['nominalRoll'])
def nominal_roll(message):
    nominal_roll = gsheet_db_func.generate_nominal_roll()
    bot.reply_to(message, nominal_roll)

def update_message_check(message):
    msg_list = message.split("\n")
    table_dict = {"STATUS:":"ms","DUTY:":"duty",
                  "LEAVE:":"leave","MA:":"ma",
                  "COURSE:":"course","OTHERS:":"others",
                  "RSI:":"rsi","RSO:":"rso",
                  "STATUS":"ms","DUTY":"duty",
                  "LEAVE":"leave","MA":"ma",
                  "COURSE":"course","OTHERS":"others",
                  "RSI":"rsi","RSO":"rso",
                  "MASS UPDATE DUTY":"duty",
                  "MASS UPDATE COURSE":"course",
                  "MASS UPDATE LEAVE":"leave","ORD": "ord"}
    if msg_list[0].strip().upper() in table_dict.keys():
        return table_dict[msg_list[0].strip().upper()]
    return

def parse_updates(msg_list):
    result = []
    for msg in msg_list:
        msg_items = msg.split(" ")
        if msg_items[0].upper() == "UPDATE":
            parsed_msg = " ".join(msg_items[1:])
            delete_items = parsed_msg.split(" (")[0]
            delete_msg = "DELETE " + delete_items
            result.append(delete_msg)
            result.append(parsed_msg)
        else:
            result.append(msg)
    return result

def parse_update_message(message):
    msg_list = message.strip().split("\n")
    table_dict = {"STATUS:":"ms","DUTY:":"duty",
                  "LEAVE:":"leave","MA:":"ma",
                  "COURSE:":"course","OTHERS:":"others",
                  "RSI:":"rsi","RSO:":"rso",
                  "STATUS":"ms","DUTY":"duty",
                  "LEAVE":"leave","MA":"ma",
                  "COURSE":"course","OTHERS":"others",
                  "RSI":"rsi","RSO":"rso",
                  "ORD": "ord"}
    mass_update_dict = {
                  "MASS UPDATE DUTY":"duty",
                  "MASS UPDATE COURSE":"course",
                  "MASS UPDATE LEAVE":"leave"}
    if msg_list[0].strip().upper() in table_dict.keys():
        return parse_updates(msg_list[1:]), False
    elif msg_list[0].strip().upper() in mass_update_dict.keys():
        return parse_updates(msg_list[1:]), True
    else:
        return parse_updates(msg_list), False

@bot.message_handler(func=lambda msg:True)
def reply_compliments(message):
    tz = pytz.timezone('Asia/Singapore')
    now = datetime.now(tz)
    msg = message.text
    check = update_message_check(msg)
    if check:
        result_handler(message, check)
        return
    if "unslay" in msg.lower():
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, "static/images")
        slays = ["zackslaying.gif", "zackslaying1.gif", "zackslaying2.gif", "zackslaying3.gif"]
        slay_file_path = os.path.join(file_path, random.choice(slays))
        zack_slay_animation = open(slay_file_path,"rb")
        bot.reply_to(message, "no zackaria you must slay")
        bot.send_document(chat_id=message.chat.id,message_thread_id=message.message_thread_id,document=zack_slay_animation)
    elif "slay" in msg.lower():
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(BASE_DIR, "static/images")
        slays = ["zackslaying.gif", "zackslaying1.gif", "zackslaying2.gif", "zackslaying3.gif"]
        slay_file_path = os.path.join(file_path, random.choice(slays))
        zack_slay_animation = open(slay_file_path,"rb")
        bot.reply_to(message, "yes zackaria slayy 💅")
        bot.send_document(chat_id=message.chat.id,message_thread_id=message.message_thread_id,document=zack_slay_animation)
    elif "poggers" in msg.lower():
        bot.reply_to(message, "holy fking poggers the code works man")
    elif "good bot" in msg.lower():
        bot.reply_to(message, "thx, of course everything is working as intended, surely nothing breaks")
    elif "bad bot" in msg.lower():
        bot.reply_to(message, "noted.")
        user = message.from_user
        username = user.username
        full_name = user.full_name
        today = now.strftime("%d/%m/%y")
        now += timedelta(hours=2)
        time_now = now.strftime("%H%M")
        reply_msg = "Convict Code Name: {}, Full Name: {}\nTime of arrest: {} {} IP Address: xxx.xxx.xxx"
        bot.reply_to(message, reply_msg.format(username,full_name.capitalize(),time_now,today))
    elif "watch this" in msg.lower():
        bot.reply_to(message, "im watching")
    elif "cow" in msg.lower():
        bot.reply_to(message, "J🐮: mooooo~")
        cow_gifs = ["NEW_COW.gif"]
        gif = random.choice(cow_gifs)
        if gif[:5] != "https":
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(BASE_DIR, "static/images")
            gif_path = os.path.join(file_path, gif)
            gif = open(gif_path, "rb")
        bot.send_document(chat_id=message.chat.id,message_thread_id=message.message_thread_id,document=gif)
    #elif "scary" in msg.lower():
        #bot.reply_to(message, "im not scary im just artificial bits of data on the internet")
        #time.sleep(3)
        #bot.send_message(chat_id=message.chat.id,message_thread_id=message.message_thread_id,text="as artificial as the end date to justin's bulking season")
    #elif "thats crazy" in msg.lower():
        #bot.reply_to(message, "its not crazy bruh its the nav-")
        #bot.send_animation(chat_id=message.chat.id,message_thread_id=message.message_thread_id,animation="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMGdpZHdqMGQxeXB6MmhsZWRiZWhwMGtiY3Q1a3d3amZkcXdpbGR4eCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/jQcTvFdi1DUSclonUc/giphy.gif")

if __name__ == "__main__":
    bot.infinity_polling()