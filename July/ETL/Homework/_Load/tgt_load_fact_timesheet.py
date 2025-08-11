from dotenv import load_dotenv
import os
from datetime import date
import oracledb

# --- Credentialele pentru target din .env ---
load_dotenv()
TGT_USER      = os.getenv("ORACLE_USER_TGT")
TGT_PASSWORD  = os.getenv("ORACLE_PASSWORD_TGT")
DSN           = os.getenv("ORACLE_DSN")

BASE_TIMESHEET_ID = 21010
PROJECT_ID        = 1      # puteai de asemenea să-l interoghezi din DIM_TGT_PROJECT
WORKED_HOURS      = 8.0
DU_LIST           = ['Suceava', 'Brasov']
DATE_FROM         = date(2025, 6, 1)
DATE_TO           = date(2025, 7, 31)

def get_next_timesheet_id(cur):
    cur.execute("SELECT NVL(MAX(timesheetID),0) FROM FACT_TGT_TIMESHEET")
    (m,) = cur.fetchone()
    return m+1 if m>0 else BASE_TIMESHEET_ID

def fetch_two_employees(cur, du):
    cur.execute("""
        SELECT employeeHistoryID
          FROM (
            SELECT employeeHistoryID
              FROM DIM_TGT_EMPLOYEE_HISTORY
             WHERE du = :du
             ORDER BY employeeHistoryID
          )
         WHERE ROWNUM <= 5
    """, du=du)
    return [row[0] for row in cur.fetchall()]

def fetch_dates(cur):
    cur.execute("""
        SELECT dateID
          FROM DIM_TGT_DATE
         WHERE fullDate BETWEEN :dfrom AND :dto
         ORDER BY fullDate
    """, dfrom=DATE_FROM, dto=DATE_TO)
    return [row[0] for row in cur.fetchall()]

def fetch_absence_id_R(cur):
    cur.execute("""
        SELECT absenceID
          FROM DIM_TGT_ABSENCES
         WHERE absenceCode = 'R'
    """)
    row = cur.fetchone()
    if not row:
        raise RuntimeError("Nu există absenceCode='R' în DIM_TGT_ABSENCES")
    return row[0]

def main():
    conn = oracledb.connect(user=TGT_USER, password=TGT_PASSWORD, dsn=DSN)
    cur  = conn.cursor()
    try:
        next_id      = get_next_timesheet_id(cur)
        absence_id_r = fetch_absence_id_R(cur)
        emp_ids      = []
        for du in DU_LIST:
            emp_ids += fetch_two_employees(cur, du)
        date_ids     = fetch_dates(cur)

        records = []
        for emp_hist_id in emp_ids:
            for date_id in date_ids:
                records.append([
                    next_id,
                    emp_hist_id,
                    date_id,
                    absence_id_r,
                    PROJECT_ID,
                    WORKED_HOURS
                ])
                next_id += 1

        if records:
            cur.executemany("""
                INSERT INTO FACT_TGT_TIMESHEET
                  (timesheetID, employeeHistoryID,
                   dateID, absenceID, projectID, workedHours)
                VALUES (:1, :2, :3, :4, :5, :6)
            """, records)
            conn.commit()
            print(f"Inserted {len(records)} rows, IDs {records[0][0]}–{records[-1][0]}")
        else:
            print("Nu sunt rânduri de inserat.")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
