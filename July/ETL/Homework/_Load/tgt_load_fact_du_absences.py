from dotenv import load_dotenv
import os
from datetime import date
import oracledb

# --- Încarcă credentialele ---
load_dotenv()
STG_USER      = os.getenv("ORACLE_USER_STG")
STG_PASSWORD  = os.getenv("ORACLE_PASSWORD_STG")
TGT_USER      = os.getenv("ORACLE_USER_TGT")
TGT_PASSWORD  = os.getenv("ORACLE_PASSWORD_TGT")
DSN           = os.getenv("ORACLE_DSN")

BASE_FACT_ID  = 11010
PROJECT_ID    = 1

def get_next_fact_id(cur):
    cur.execute("SELECT NVL(MAX(duAbsenceID),0) FROM FACT_TGT_DU_ABSENCES")
    (m,) = cur.fetchone()
    return m + 1 if m > 0 else BASE_FACT_ID

def build_employee_history_map(cur):
    cur.execute("SELECT employeeHistoryID, employeeName FROM DIM_TGT_EMPLOYEE_HISTORY")
    return {name: eid for eid, name in cur.fetchall()}

def build_date_map(cur):
    cur.execute("SELECT dateID, fullDate FROM DIM_TGT_DATE")
    mp = {}
    for did, dt in cur.fetchall():
        # dt is datetime.datetime; convert to date
        mp[dt.date()] = did
    return mp

def build_absence_code_map(cur):
    cur.execute("SELECT absenceID, absenceCode FROM DIM_TGT_ABSENCES")
    return {code: aid for aid, code in cur.fetchall()}

def build_stage_code_map(cur):
    cur.execute("SELECT absenceCodeID, absenceCode FROM DIM_STG_DU_ABSENCE_CODES")
    return {cid: code for cid, code in cur.fetchall()}

def fetch_stage_absences(cur):
    cur.execute("""
        SELECT absenceID,
               employeeName,
               absenceCodeID,
               absenceDate,
               du
          FROM DIM_STG_DU_ABSENCES
         ORDER BY absenceID
    """)
    return cur.fetchall()

def main():
    # deschidem conexiunile
    stg_conn = oracledb.connect(user=STG_USER, password=STG_PASSWORD, dsn=DSN)
    tgt_conn = oracledb.connect(user=TGT_USER, password=TGT_PASSWORD, dsn=DSN)
    stg_cur  = stg_conn.cursor()
    tgt_cur  = tgt_conn.cursor()

    try:
        # construim mapările
        emp_hist_map    = build_employee_history_map(tgt_cur)
        date_map        = build_date_map(tgt_cur)
        tgt_code_map    = build_absence_code_map(tgt_cur)
        stage_code_map  = build_stage_code_map(stg_cur)

        # preluăm rândurile staging
        stg_rows = fetch_stage_absences(stg_cur)

        # generăm fact rows
        next_fact_id = get_next_fact_id(tgt_cur)
        records = []
        for (_stg_id, emp_name, code_id, full_dt, du) in stg_rows:
            # employeeHistoryID
            eh_id = emp_hist_map.get(emp_name)
            if eh_id is None:
                continue  # nume necunoscut

            # dateID
            d = full_dt.date()
            date_id = date_map.get(d)
            if date_id is None:
                continue  # data necunoscută

            # absenceID
            code_str = stage_code_map.get(code_id)
            abs_id   = tgt_code_map.get(code_str)
            if abs_id is None:
                continue  # cod necunoscut

            records.append([
                next_fact_id,
                eh_id,
                abs_id,
                date_id,
                PROJECT_ID,
                du
            ])
            next_fact_id += 1

        # inserăm în fact
        if records:
            tgt_cur.executemany("""
                INSERT INTO FACT_TGT_DU_ABSENCES
                  (duAbsenceID, employeeHistoryID,
                   absenceID, dateID, projectID, du)
                VALUES
                  (:1, :2, :3, :4, :5, :6)
            """, records)
            tgt_conn.commit()
            print(f"Inserted {len(records)} rows into FACT_TGT_DU_ABSENCES, IDs {records[0][0]}–{records[-1][0]}")
        else:
            print("No records to insert.")

    finally:
        stg_cur.close()
        tgt_cur.close()
        stg_conn.close()
        tgt_conn.close()

if __name__ == "__main__":
    main()
