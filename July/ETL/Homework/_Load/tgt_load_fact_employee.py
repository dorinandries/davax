from dotenv import load_dotenv
import os
import oracledb
from datetime import date

# --- Încarcă credențialele din .env ---
load_dotenv()
SRC_USER     = os.getenv("ORACLE_USER_STG")
SRC_PASSWORD = os.getenv("ORACLE_PASSWORD_STG")
TGT_USER     = os.getenv("ORACLE_USER_TGT")
TGT_PASSWORD = os.getenv("ORACLE_PASSWORD_TGT")
DSN          = os.getenv("ORACLE_DSN")

# Parametri pentru FACT_TGT_EMPLOYEE
BASE_EMP_ID    = 7110
GRADE          = "DT"
DISCIPLINE     = "Data & AI"
MANAGERS       = {"Suceava": "Mariana Apastinei",
                  "Brasov":  "Petrisor Dima"}

# Parametri pentru history
BASE_HIST_ID   = BASE_EMP_ID + 1000
HIST_START     = date(2025, 6, 1)
HIST_END       = date(2099, 1, 1)
IS_ACTIVE      = 'Y'

def get_next_id(cur, table, pk_col, base):
    cur.execute(f"SELECT NVL(MAX({pk_col}),0) FROM {table}")
    (m,) = cur.fetchone()
    return m + 1 if m > 0 else base

def fetch_stg_employees(cur):
    """Preia toate rândurile din DIM_STG_EMPLOYEE"""
    cur.execute("""
        SELECT employeeID,
               employeeName,
               employeeEmail,
               grade,
               disciplineName,
               lineManager,
               du
          FROM DIM_STG_EMPLOYEE
    """)
    return cur.fetchall()

def fetch_existing_facts(cur):
    """Chei naturale existente în FACT_TGT_EMPLOYEE"""
    cur.execute("""
        SELECT employeeName,
               employeeEmail,
               grade,
               disciplineName,
               lineManager,
               du
          FROM FACT_TGT_EMPLOYEE
    """)
    return {tuple(r) for r in cur.fetchall()}

def fetch_existing_history(cur):
    """Tuple existente în DIM_TGT_EMPLOYEE_HISTORY"""
    cur.execute("""
        SELECT employeeID,
               startDate,
               endDate,
               isActive
          FROM DIM_TGT_EMPLOYEE_HISTORY
    """)
    return {tuple(r) for r in cur.fetchall()}

def insert_fact_employees(stg_rows, tgt_cur):
    existing = fetch_existing_facts(tgt_cur)
    next_id  = get_next_id(tgt_cur, "FACT_TGT_EMPLOYEE", "employeeID", BASE_EMP_ID)
    new_ids  = []

    records = []
    for _stg_empID, name, email, grade, disc, lm, du in stg_rows:
        key = (name, email, grade, disc, lm, du)
        if key in existing:
            continue
        records.append((next_id, name, email, grade, disc, lm, du))
        existing.add(key)
        new_ids.append(next_id)
        next_id += 1

    if records:
        tgt_cur.executemany("""
            INSERT INTO FACT_TGT_EMPLOYEE
              (employeeID, employeeName, employeeEmail,
               grade, disciplineName, lineManager, du)
            VALUES (:1,:2,:3,:4,:5,:6,:7)
        """, records)

    return new_ids

def insert_employee_history(new_emp_ids, tgt_cur):
    if not new_emp_ids:
        return 0

    existing = fetch_existing_history(tgt_cur)
    next_id  = get_next_id(tgt_cur, "DIM_TGT_EMPLOYEE_HISTORY",
                           "employeeHistoryID", BASE_HIST_ID)
    # Aducem detalii din FACT pentru noii angajați
    id_list = ",".join(str(i) for i in new_emp_ids)
    tgt_cur.execute(f"""
        SELECT employeeID,
               employeeName,
               employeeEmail,
               grade,
               disciplineName,
               lineManager,
               du
          FROM FACT_TGT_EMPLOYEE
         WHERE employeeID IN ({id_list})
    """)
    rows = tgt_cur.fetchall()

    records = []
    for empID, name, email, grade, disc, lm, du in rows:
        key = (empID, HIST_START, HIST_END, IS_ACTIVE)
        if key in existing:
            continue
        records.append((next_id,
                        empID,
                        name,
                        email,
                        grade,
                        disc,
                        lm,
                        du,
                        HIST_START,
                        HIST_END,
                        IS_ACTIVE))
        existing.add(key)
        next_id += 1

    if records:
        tgt_cur.executemany("""
            INSERT INTO DIM_TGT_EMPLOYEE_HISTORY
              (employeeHistoryID,
               employeeID,
               employeeName,
               employeeEmail,
               grade,
               disciplineName,
               lineManager,
               du,
               startDate,
               endDate,
               isActive)
            VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11)
        """, records)

    return len(records)

def main():
    # deschidem conexiunea țintă
    tgt_conn = oracledb.connect(user=TGT_USER, password=TGT_PASSWORD, dsn=DSN)
    stg_conn = oracledb.connect(user=SRC_USER, password=SRC_PASSWORD, dsn=DSN)
    try:
        stg_cur = stg_conn.cursor()
        tgt_cur = tgt_conn.cursor()

        # 1) preluăm din staging employee
        stg_rows = fetch_stg_employees(stg_cur)

        # 2) inserăm FACT_TGT_EMPLOYEE
        new_ids = insert_fact_employees(stg_rows, tgt_cur)
        print(f"→ Inserate {len(new_ids)} rânduri în FACT_TGT_EMPLOYEE")
        tgt_conn.commit()

        # 3) inserăm DIM_TGT_EMPLOYEE_HISTORY
        cnt_hist = insert_employee_history(new_ids, tgt_cur)
        print(f"→ Inserate {cnt_hist} rânduri în DIM_TGT_EMPLOYEE_HISTORY")
        tgt_conn.commit()
    finally:
        stg_cur.close()
        tgt_cur.close()
        stg_conn.close()
        tgt_conn.close()

if __name__ == "__main__":
    main()
