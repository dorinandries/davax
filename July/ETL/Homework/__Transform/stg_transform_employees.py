from dotenv import load_dotenv
import os
import oracledb

# --- Încarcă credențialele din .env ---
load_dotenv()
SRC_USER     = os.getenv("ORACLE_USER_SRC")
SRC_PASSWORD = os.getenv("ORACLE_PASSWORD_SRC")
STG_USER     = os.getenv("ORACLE_USER_STG")
STG_PASSWORD = os.getenv("ORACLE_PASSWORD_STG")
DSN           = os.getenv("ORACLE_DSN")

# Parametri de business
BASE_EMP_ID   = 6110
GRADE         = "DT"
DISCIPLINE    = "Data & AI"
MANAGERS      = {"Suceava": "Mariana Apastinei",
                 "Brasov":  "Petrisor Dima"}

def get_next_id(cur, table, pk_col, base):
    cur.execute(f"SELECT NVL(MAX({pk_col}),0) FROM {table}")
    (m,) = cur.fetchone()
    return m + 1 if m > 0 else base

def fetch_raw_employees(src_cur):
    """Preia numele și DU distincte nenule din raw absences."""
    src_cur.execute("""
        SELECT DISTINCT employeeName, du
          FROM DIM_RAW_DU_ABSENCES
         WHERE employeeName IS NOT NULL
    """)
    return src_cur.fetchall()

def fetch_training_emails(stg_cur):
    """Construiește mapping employeeName → employeeEmail din training."""
    stg_cur.execute("""
        SELECT employeeName, employeeEmail
          FROM DIM_STG_EMPLOYEES_ON_TRAINING
    """)
    return dict(stg_cur.fetchall())

def fetch_existing_employees(stg_cur):
    """Set de tuple pentru a evita duplicate în staging."""
    stg_cur.execute("""
        SELECT employeeName, employeeEmail, grade, disciplineName, lineManager, du
          FROM DIM_STG_EMPLOYEE
    """)
    return {tuple(r) for r in stg_cur.fetchall()}

def insert_stg_employee(src_cur, stg_cur):
    raw_rows    = fetch_raw_employees(src_cur)
    email_map   = fetch_training_emails(stg_cur)
    existing    = fetch_existing_employees(stg_cur)
    next_id     = get_next_id(stg_cur, "DIM_STG_EMPLOYEE", "employeeID", BASE_EMP_ID)

    records = []
    for name, du in raw_rows:
        email    = email_map.get(name)
        line_mgr = MANAGERS.get(du)
        key      = (name, email, GRADE, DISCIPLINE, line_mgr, du)
        if key in existing:
            continue
        records.append((next_id, name, email, GRADE, DISCIPLINE, line_mgr, du))
        existing.add(key)
        next_id += 1

    if records:
        stg_cur.executemany("""
            INSERT INTO DIM_STG_EMPLOYEE
              (employeeID, employeeName, employeeEmail,
               grade, disciplineName, lineManager, du)
            VALUES (:1,:2,:3,:4,:5,:6,:7)
        """, records)

    return len(records)

def main():
    # Conexiuni
    src_conn = oracledb.connect(user=SRC_USER,     password=SRC_PASSWORD, dsn=DSN)
    stg_conn = oracledb.connect(user=STG_USER,     password=STG_PASSWORD, dsn=DSN)
    try:
        src_cur = src_conn.cursor()
        stg_cur = stg_conn.cursor()

        count = insert_stg_employee(src_cur, stg_cur)
        stg_conn.commit()
        print(f"→ Inserate {count} rânduri noi în DIM_STG_EMPLOYEE")
    finally:
        src_cur.close()
        stg_cur.close()
        src_conn.close()
        stg_conn.close()

if __name__ == "__main__":
    main()
