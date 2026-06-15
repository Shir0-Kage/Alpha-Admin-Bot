-- Database tables for the bot. Run with "python init_db.py" or
-- "sqlite3 alpha.db < schema.sql". Safe to re-run, existing tables are kept.
--
-- Dates are TEXT in yymmdd format (240115), or 'PERMANENT' / '' for open-ended.
-- InCamp/StayOut are the text 'True' / 'False'.

-- one row per soldier
CREATE TABLE IF NOT EXISTS "SoldierInfo" (
    "SoldierID" TEXT,
    "Rank"      TEXT,
    "Name"      TEXT,
    "PLT"       TEXT,
    "GRP"       TEXT,   -- Officer / WOSPEC / Enlistees / Support Staff
    "SCT"       TEXT,   -- 4 digit service code (4D)
    "StayOut"   TEXT,
    PRIMARY KEY("SoldierID")
);

-- current first/last parade attendance
CREATE TABLE IF NOT EXISTS "Attendance" (
    "SoldierID" TEXT,
    "InCamp"    TEXT,
    PRIMARY KEY("SoldierID"),
    FOREIGN KEY("SoldierID") REFERENCES "SoldierInfo"("SoldierID")
);

-- book in/out attendance snapshot
CREATE TABLE IF NOT EXISTS "BiboAttendance" (
    "SoldierID" TEXT,
    "InCamp"    TEXT,
    PRIMARY KEY("SoldierID"),
    FOREIGN KEY("SoldierID") REFERENCES "SoldierInfo"("SoldierID")
);

CREATE TABLE IF NOT EXISTS "MedicalStatus" (
    "SoldierID"     TEXT,
    "MedicalStatus" TEXT,
    "DateFrom"      TEXT,
    "DateTo"        TEXT,
    "Remarks"       TEXT,
    PRIMARY KEY("SoldierID","DateFrom","DateTo","MedicalStatus"),
    FOREIGN KEY("SoldierID") REFERENCES "SoldierInfo"("SoldierID")
);

CREATE TABLE IF NOT EXISTS "MedicalAppointment" (
    "SoldierID" TEXT,
    "Date"      TEXT,
    "Remarks"   TEXT,
    PRIMARY KEY("SoldierID","Date"),
    FOREIGN KEY("SoldierID") REFERENCES "SoldierInfo"("SoldierID")
);

CREATE TABLE IF NOT EXISTS "Leave" (
    "SoldierID" TEXT,
    "Country"   TEXT,   -- LOCAL / OFF / overseas country
    "DateFrom"  TEXT,
    "DateTo"    TEXT,
    "Remarks"   TEXT,
    PRIMARY KEY("SoldierID","DateFrom","DateTo")
);

CREATE TABLE IF NOT EXISTS "OnCourse" (
    "SoldierID"  TEXT,
    "CourseName" TEXT,
    "DateFrom"   TEXT,
    "DateTo"     TEXT,
    "Remarks"    TEXT,
    PRIMARY KEY("SoldierID","DateFrom","DateTo"),
    FOREIGN KEY("SoldierID") REFERENCES "SoldierInfo"("SoldierID")
);

CREATE TABLE IF NOT EXISTS "Duty" (
    "SoldierID" TEXT,
    "Date"      TEXT,
    "DutyType"  TEXT,
    "Remarks"   TEXT,
    PRIMARY KEY("SoldierID","Date"),
    FOREIGN KEY("SoldierID") REFERENCES "SoldierInfo"("SoldierID")
);

-- catch all: AWOL / DB / CC / CA / RSO / compassionate etc
CREATE TABLE IF NOT EXISTS "Others" (
    "SoldierID" TEXT,
    "Reason"    TEXT,
    "DateFrom"  TEXT,
    "DateTo"    TEXT,
    "InCamp"    TEXT,
    "Remarks"   TEXT,
    PRIMARY KEY("SoldierID","Reason","DateFrom","DateTo"),
    FOREIGN KEY("SoldierID") REFERENCES "SoldierInfo"("SoldierID")
);

-- reporting sick, one open record per soldier
CREATE TABLE IF NOT EXISTS "ReportingSick" (
    "SoldierID" TEXT,
    "Location"  TEXT,   -- RSI / RSO
    "Remarks"   TEXT,
    PRIMARY KEY("SoldierID"),
    FOREIGN KEY("SoldierID") REFERENCES "SoldierInfo"("SoldierID")
);

CREATE TABLE IF NOT EXISTS "RationType" (
    "SoldierID" TEXT,
    "Ration"    TEXT,
    PRIMARY KEY("SoldierID"),
    FOREIGN KEY("SoldierID") REFERENCES "SoldierInfo"("SoldierID")
);

-- parade state grouping. GroupTag is matched against SoldierInfo.PLT with LIKE.
-- seed it for your unit, see seed_groups.sql
CREATE TABLE IF NOT EXISTS "GroupSettings" (
    "GroupID"   INTEGER,
    "GroupName" TEXT,
    "GroupTag"  TEXT,
    PRIMARY KEY("GroupID" AUTOINCREMENT)
);
