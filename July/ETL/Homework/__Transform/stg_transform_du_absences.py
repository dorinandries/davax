from dotenv import load_dotenv
import os, sys
import oracledb
from datetime import date

# --- Încarcă și validează credențialele ---
load_dotenv()
SRC_USER     = os.getenv("ORACLE_USER_SRC", "")
SRC_PASSWORD = os.getenv("ORACLE_PASSWORD_SRC", "")
STG_USER     = os.getenv("ORACLE_USER_STG", "")
STG_PASSWORD = os.getenv("ORACLE_PASSWORD_STG", "")
DSN          = os.getenv("ORACLE_DSN", "")

for name, val in [
    ("ORACLE_USER_SRC", SRC_USER),
    ("ORACLE_PASSWORD_SRC", SRC_PASSWORD),
    ("ORACLE_USER_STG", STG_USER),
    ("ORACLE_PASSWORD_STG", STG_PASSWORD),
    ("ORACLE_DSN", DSN),
]:
    if not val:
        print(f"‼️ Obiectul de mediu {name} nu este setat!")
        sys.exit(1)

# --- Funcții pentru SRC (citire raw) ---
def test_src_conn():
    try:
        conn = oracledb.connect(user=SRC_USER, password=SRC_PASSWORD, dsn=DSN)
        conn.close()
        print("✅ Conexiune SRC OK")
    except oracledb.DatabaseError as e:
        print(f"❌ Eroare la conectarea SRC ({SRC_USER}/****): {e}")
        sys.exit(1)

def fetch_distinct_raw_codes():
    conn = oracledb.connect(user=SRC_USER, password=SRC_PASSWORD, dsn=DSN)
    cur  = conn.cursor()
    cur.execute("""
        SELECT DISTINCT absenceCode, absenceDescription
          FROM DIM_RAW_DU_ABSENCES
         WHERE absenceCode IS NOT NULL
           AND absenceDescription IS NOT NULL
    """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return data

def fetch_raw_absences():
    conn = oracledb.connect(user=SRC_USER, password=SRC_PASSWORD, dsn=DSN)
    cur  = conn.cursor()
    cur.execute("""
        SELECT absenceID, employeeName, absenceCode, day, month, year, du
          FROM DIM_RAW_DU_ABSENCES
         WHERE absenceCode IS NOT NULL
           AND absenceDescription IS NOT NULL
         ORDER BY absenceID
    """)
    data = cur.fetchall()
    cur.close(); conn.close()
    return data

# --- Funcții pentru STG (scriere staging) ---
def test_stg_conn():
    try:
        conn = oracledb.connect(user=STG_USER, password=STG_PASSWORD, dsn=DSN)
        conn.close()
        print("✅ Conexiune STG OK")
    except oracledb.DatabaseError as e:
        print(f"❌ Eroare la conectarea STG ({STG_USER}/****): {e}")
        sys.exit(1)

def get_next_code_id(cur):
    cur.execute("SELECT NVL(MAX(absenceCodeID),0) FROM DIM_STG_DU_ABSENCE_CODES")
    (m,) = cur.fetchone()
    return m + 1

def fetch_existing_codes(cur):
    cur.execute("SELECT absenceCode FROM DIM_STG_DU_ABSENCE_CODES")
    return {r[0] for r in cur.fetchall()}

def insert_new_codes(cur, codes):
    next_id = get_next_code_id(cur)
    recs = []
    for code, desc in codes:
        recs.append((next_id, code, desc))
        next_id += 1
    print(recs)
    if recs:
        cur.executemany("""
            INSERT INTO DIM_STG_DU_ABSENCE_CODES
              (absenceCodeID, absenceCode, absenceDescription)
            VALUES (:1, :2, :3)
        """, recs)
    return len(recs)

def build_code_map(cur):
    cur.execute("SELECT absenceCode, absenceCodeID FROM DIM_STG_DU_ABSENCE_CODES")
    return {code: cid for code, cid in cur.fetchall()}

def insert_staging_absences(cur, code_map, raw_rows):
    # determină next absenceID
    cur.execute("SELECT NVL(MAX(absenceID),0) FROM DIM_STG_DU_ABSENCES")
    (m,) = cur.fetchone()
    next_id = m + 1 if m>0 else 3110

    recs = []
    for abs_id, emp, code, d, m_, y, du in raw_rows:
        cid = code_map.get(code)
        if not cid:
            continue
        absence_date = date(y, m_, d)
        recs.append((next_id, emp, cid, absence_date, du))
        next_id += 1

    if recs:
        cur.executemany("""
            INSERT INTO DIM_STG_DU_ABSENCES
              (absenceID, employeeName, absenceCodeID, absenceDate, du)
            VALUES (:1,:2,:3,:4,:5)
        """, recs)
    return len(recs)

def main():
    # 1. Testăm conexiunile
    test_src_conn()
    test_stg_conn()

    # 2. Luăm codurile DISTINCT din RAW
    raw_codes = fetch_distinct_raw_codes()

    # 3. Deschidem sesiunea STG
    stg_conn = oracledb.connect(user=STG_USER, password=STG_PASSWORD, dsn=DSN)
    stg_cur  = stg_conn.cursor()

    # 4. Inserăm codurile noi
    existing = fetch_existing_codes(stg_cur)
    new_codes = [c for c in raw_codes if c[0] not in existing]
    cnt1 = insert_new_codes(stg_cur, new_codes)
    print(f"→ Inserate {cnt1} coduri noi în DIM_STG_DU_ABSENCE_CODES")
    stg_conn.commit()

    # 5. Map și citim raw-rows (SRC!)
    code_map = build_code_map(stg_cur)
    raw_rows = fetch_raw_absences()

    # 6. Inserăm absențele normalizate
    cnt2 = insert_staging_absences(stg_cur, code_map, raw_rows)
    print(f"→ Inserate {cnt2} rânduri în DIM_STG_DU_ABSENCES")
    stg_conn.commit()

    # 7. Închidem conexiunea STG
    stg_cur.close()
    stg_conn.close()

if __name__ == "__main__":
    main()
