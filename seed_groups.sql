-- Example grouping for the parade state. GroupTag is matched against
-- SoldierInfo.PLT with LIKE, so "P1S1" hits platoon 1 section 1, "Coy HQ%"
-- hits all the Coy HQ sub units. Edit these rows for your own unit.
-- Only loaded when GroupSettings is empty (python init_db.py --seed-groups).

INSERT INTO "GroupSettings" ("GroupName", "GroupTag") VALUES
    ('Coy HQ',                'Coy HQ'),
    ('SUPPORT STAFF SECTION', 'Coy HQ SSP'),
    ('STEELNET SECTION',      'Coy HQ SN'),
    ('ANTI-TANK SECTION',     'Coy HQ MPATS'),
    ('MARKSMAN SECTION',      'Coy HQ MM'),
    ('PLT 1 HQ',              'P1 HQ'),
    ('PLT 1 SCT 1',           'P1S1'),
    ('PLT 1 SCT 2',           'P1S2'),
    ('PLT 2 HQ',              'P2 HQ'),
    ('PLT 2 SCT 1',           'P2S1'),
    ('PLT 2 SCT 2',           'P2S2'),
    ('PLT 3 HQ',              'P3 HQ'),
    ('PLT 3 SCT 1',           'P3S1'),
    ('PLT 3 SCT 2',           'P3S2'),
    ('PLT 4 HQ',              'P4 HQ'),
    ('PLT 4 SCT 1',           'P4S1'),
    ('PLT 4 SCT 2',           'P4S2'),
    ('PLT 5 HQ',              'P5 HQ'),
    ('PLT 5 SCT 1',           'P5S1'),
    ('PLT 5 SCT 2',           'P5S2'),
    ('SHARK PLT 1 HQ',        'SP HQ'),
    ('SHARK PLT 1 SCT 1',     'SP1S1'),
    ('SHARK PLT 1 SCT 2',     'SP1S2'),
    ('SHARK PLT 2 SCT 1',     'SP2S1'),
    ('SHARK PLT 2 SCT 2',     'SP2S2');
