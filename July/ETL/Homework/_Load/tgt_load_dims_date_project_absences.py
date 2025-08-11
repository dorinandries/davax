from dotenv import load_dotenv
import os
import oracledb
from datetime import date, timedelta

# --- Încarcă credențialele din .env ---
load_dotenv()
STG_USER     = os.getenv("ORACLE_USER_STG")
STG_PASSWORD = os.getenv("ORACLE_PASSWORD_STG")
TGT_USER     = os.getenv("ORACLE_USER_TGT")
TGT_PASSWORD = os.getenv("ORACLE_PASSWORD_TGT")
DSN          = os.getenv("ORACLE_DSN")

# Interval de procesat pentru DIM_TGT_DATE
START_DATE   = date(2025, 5, 1)
END_DATE     = date(2025, 8, 31)
BASE_DATE_ID = 1

# Proiecte pentru DIM_TGT_PROJECT
BASE_PROJECT_ID = 1
PROJECTS = [
    "DavaX.Academy Data",
    "DavaX.Academy Development",
    "DavaX.Academy DevOps"
]

# Setare pentru absențe
BASE_ABS_ID = 1


def get_next_id(cur, table, pk_col, base):
    # dacă tabela e goală, începe de la base, altfel max(pk_col)+1
    cur.execute(f"SELECT COUNT(*), NVL(MAX({pk_col}),0) FROM {table}")
    count, max_val = cur.fetchone()
    if count == 0:
        return base
    return max_val + 1

    cur.execute(f"SELECT NVL(MAX({pk_col}),0) FROM {table}")
    (max_val,) = cur.fetchone()
    return max_val + 1 if max_val > 0 else base


def populate_date_dim(tgt_cur):
    # Ia toate datele deja existente
    tgt_cur.execute("SELECT fullDate FROM DIM_TGT_DATE")
    existing_dates = {row[0] for row in tgt_cur.fetchall()}

    next_id = get_next_id(tgt_cur, "DIM_TGT_DATE", "dateID", BASE_DATE_ID)
    to_insert = []
    current = START_DATE
    while current <= END_DATE:
        if current not in existing_dates:
            dow = current.strftime("%A")
            weekend_flag = 'Y' if current.weekday() >= 5 else 'N'
            to_insert.append((
                next_id,
                current,
                current.day,
                current.month,
                current.year,
                dow,
                weekend_flag
            ))
            next_id += 1
        current += timedelta(days=1)

    if to_insert:
        tgt_cur.executemany(
            """
            INSERT INTO DIM_TGT_DATE
              (dateID, fullDate, day, month, year, dayOfWeek, isWeekend)
            VALUES (:1,:2,:3,:4,:5,:6,:7)
            """,
            to_insert
        )
    return len(to_insert)


def populate_project_dim(tgt_cur):
    tgt_cur.execute("SELECT projectDescription FROM DIM_TGT_PROJECT")
    existing = {row[0] for row in tgt_cur.fetchall()}
    next_id = get_next_id(tgt_cur, "DIM_TGT_PROJECT", "projectID", BASE_PROJECT_ID)
    to_insert = [(next_id + i, proj) for i, proj in enumerate(PROJECTS) if proj not in existing]

    if to_insert:
        tgt_cur.executemany(
            """
            INSERT INTO DIM_TGT_PROJECT (projectID, projectDescription)
            VALUES (:1, :2)
            """, to_insert
        )
    return len(to_insert)


def populate_absences_dim(stg_cur, tgt_cur):
    # Preia codurile existente în staging
    stg_cur.execute("SELECT absenceCode, absenceDescription FROM DIM_STG_DU_ABSENCE_CODES")
    stg_codes = stg_cur.fetchall()

    tgt_cur.execute("SELECT absenceCode, absenceDescription FROM DIM_TGT_ABSENCES")
    existing = {tuple(r) for r in tgt_cur.fetchall()}
    next_id = get_next_id(tgt_cur, "DIM_TGT_ABSENCES", "absenceID", BASE_ABS_ID)
    to_insert = []

    for code, desc in stg_codes:
        if (code, desc) not in existing:
            to_insert.append((next_id, code, desc))
            existing.add((code, desc))
            next_id += 1
    # Adaugă în plus și codul pentru Sick
    if ('S', 'Sick') not in existing:
        to_insert.append((next_id, 'S', 'Sick'))
        next_id += 1

    if ('R', 'Regular') not in existing:
        to_insert.append((next_id, 'R', 'Regular'))
        next_id += 1

    if ('OVT', 'Overtime') not in existing:
        to_insert.append((next_id, 'OVT', 'Overtime'))
        next_id += 1

    if to_insert:
        tgt_cur.executemany(
            """
            INSERT INTO DIM_TGT_ABSENCES
              (absenceID, absenceCode, absenceDescription)
            VALUES (:1,:2,:3)
            """, to_insert
        )
    return len(to_insert)


def main():
    stg_conn = oracledb.connect(user=STG_USER, password=STG_PASSWORD, dsn=DSN)
    tgt_conn = oracledb.connect(user=TGT_USER, password=TGT_PASSWORD, dsn=DSN)
    try:
        stg_cur = stg_conn.cursor()
        tgt_cur = tgt_conn.cursor()

        cnt_dates = populate_date_dim(tgt_cur)
        print(f"→ Inserate {cnt_dates} rânduri noi în DIM_TGT_DATE")

        cnt_proj = populate_project_dim(tgt_cur)
        print(f"→ Inserate {cnt_proj} rânduri noi în DIM_TGT_PROJECT")

        cnt_abs = populate_absences_dim(stg_cur, tgt_cur)
        print(f"→ Inserate {cnt_abs} rânduri noi în DIM_TGT_ABSENCES")

        tgt_conn.commit()
    finally:
        stg_cur.close()
        tgt_cur.close()
        stg_conn.close()
        tgt_conn.close()

if __name__ == "__main__":
    main()
