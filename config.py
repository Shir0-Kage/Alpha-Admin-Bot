import gspread

PARADESTATE_FORMAT = """
A COY PARADE STRENGTH CAA {date} {time}HRS


Total Commander: {totalcommanderstr}
Total Support Staff: -/0


Grand Total: {grandtotal}
Total Officer: {totalofficer}
Total WOSE: {totalwose}


Personnel on DB/AWOL/CC/CA: 00
------------------------------------------

COY HQ
TOTAL STRENGTH: {coyhqstr}
OFFICER: {coyhqofficerstr}
{coyhqofficers}

WOSE: {coyhqwosestr}
{coyhqwose}

Commander: {coyhqstr}
Support Staff: -/0

----------------------------------------------

PLT HQ
TOTAL STRENGTH: {plthqstr}
OFFICER: -/0

WOSE: {plthqwosestr}
{plthqwose}

Commander: {plthqstr}
Support Staff: -/0

----------------------------------------------

❌ STATUS: {statusstr}
{status}

😷MC: {mcstr}
{mc}

👨🏻⚕MA: {mastr}
{ma}

🚪LEAVE: {leavestr}
{leave}

🏠STAY OUT: {stayoutstr}
{stayout}

🎓ON COURSE: {oncoursestr}
{oncourse}

🚨ON DUTY: {dutystr}
{duty}

📔OTHERS: {otherstr}
{others}
"""

HEADER_FORMAT = """
A COY PARADE STRENGTH CAA {date} {time}HRS

Total Commander: {total_commander_str}
Total Support Staff: {total_support_staff_str}
Total Troopers: {total_trooper_str}

Grand Total: {grand_total}
Total Officer: {total_officer}
Total WOSE: {total_wose}

Personnel on DB/AWOL/CC/CA: {dbAwolCcCA}
"""

DIVIDER = "-----------------------------------"

GROUP_FORMAT = """
{group_name}
TOTAL STRENGTH: {total_str}
OFFICER: {officer_str}
{officers}
WOSE: {wose_str}
{wose}
Commander: {commander_str}
"""

SUPPORT_STAFF_FORMAT = "Support Staff: {}"

TROOPER_FORMAT = "Trooper: {}"

SPECIAL_CASE_FORMAT = """
❌ STATUS: {status_str}
{status}

😷MC: {mc_str}
{mc}

👨🏻⚕MA: {ma_str}
{ma}

🚪LEAVE: {leave_str}
{leave}

🏠STAY OUT: {stayout_str}
{stayout}

🎓ON COURSE: {oncourse_str}
{oncourse}

🚨ON DUTY: {duty_str}
{duty}

📔OTHERS: {others_str}
{others}"""


RECRUIT_HEADER_FORMAT = """
{group} PARADESTATE {date} {time} HRS

Recruits Grand Total: {grand_total}
"""

COMMANDERS_GROUP_FORMAT = """
Commanders
---------------------
Total Commanders: {total_str}

Absent: {absent_strength}
{absent_nr}
"""

RECRUIT_GROUP_FORMAT = """
Total {group_name}: {group_strength}
Total S1: {s1_str}
Total S2: {s2_str}
Total S3: {s3_str}
Total S4: {s4_str}

MC: {mc_count}
{mc_nr}
RIB: {rib_count}
{rib_nr}
Status: {status_count}
{status_nr}
Status Day 1: {status_d1_count}
{status_d1_nr}
RSI: {rsi_count}
{rsi_nr}
RSO: {rso_count}
{rso_nr}
Others: {others_count}
{others_nr}
"""

BOOK_IN_STR_HEADER = """*Alpha Coy Book {in_or_out} Strength caa {date} {time}*

*Total strength: {total_coy}*
- *Commander: {total_comd}*
- *Trooper strength: {total_trooper}*
- *Support staff: {total_staff}*

"""

BOOK_IN_STR_GROUP = """*{group_name}*
{group_tag} Strength: {total_group}
-Comd: {total_comd}
{comd_absent}"""


BOOK_IN_STR_GROUP_STAFF = """-Staff: {total_staff}
{staff_absent}
"""

# removed status
BOOK_IN_STR_GROUP_TROOPER = """-Troopers: {total_trooper}
{absent}
"""

TRIPLINE_MSG = """*Alpha Coy Triplines caa {date}*
Total Monitoring: {total_monitoring} pax
Tripline 2: {tripline2_count} pax
Tripline 3: {tripline3_count} pax

*Tripline 2 - 4 to 7 Days*
{tripline2_nr}

*Tripline 3 - 8 to 11 Days*
{tripline3_nr}

 *Special absentees cases/ Problematic Personnel*
{special_case}

*Key Updates/ Actionables*
1. """


SERVICE_ACCOUNT = gspread.service_account("/home/ShiroKage/main/service_account.json")