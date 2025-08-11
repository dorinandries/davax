from dotenv import load_dotenv
import os, csv, re, time
import oracledb

# --- Variabilele de conexiune ---
load_dotenv()
USER     = os.getenv("ORACLE_USER_SRC")
PASSWORD = os.getenv("ORACLE_PASSWORD_SRC")
DSN      = os.getenv("ORACLE_DSN")

# Selectează fișierul dorit:
CSV_FILE = '../duAbsences/Dava_Suceava_May.csv'
#CSV_FILE = '../duAbsences/Dava_Suceava_June.csv'
#CSV_FILE = '../duAbsences/Dava_Brasov_May.csv'
#CSV_FILE = '../duAbsences/Dava_Brasov_June.csv'

START_ID = 1110

def get_start_id():
    """Dacă tabela are rânduri, returnează MAX(absenceID)+1, altfel START_ID."""
    conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
    cur  = conn.cursor()
    cur.execute("SELECT NVL(MAX(absenceID), 0) FROM DIM_RAW_DU_ABSENCES")
    maxid, = cur.fetchone()
    cur.close()
    conn.close()
    return maxid + 1 if maxid > 0 else START_ID

def parse_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = list(csv.reader(f))

    # 1) luna (rândul 2)
    month_cell = reader[1][0].strip()
    try:
        month = int(month_cell)
    except ValueError:
        import calendar
        month = list(calendar.month_name).index(month_cell)

    # 2) DU (rândul 3)
    du = reader[2][0].strip()

    # 3) cod <-> descriere (rândul 4)
    code_map = {}
    for i, cell in enumerate(reader[3]):
        code = cell.strip()
        if re.fullmatch(r'[A-Z0-9/]+', code):
            desc = None
            for d in reader[3][i+1:]:
                if d.strip():
                    desc = d.strip()
                    break
            code_map[code] = desc

    # 4) anul (rândul 6)
    year = None
    for cell in reader[5]:
        c = cell.strip()
        if re.fullmatch(r'\d{4}', c):
            year = int(c)
            break

    # 5) header zile (rândul 8)
    header = reader[7]
    day_indices  = [i for i, h in enumerate(header) if h.strip().isdigit()]
    day_numbers  = [int(header[i].strip()) for i in day_indices]

    # 6) index Total days
    total_idx = header.index('Total days')

    # 7) index Missing time/h — dacă lipsește, folosim None
    try:
        missing_time_idx = header.index('Missing time/h')
    except ValueError:
        missing_time_idx = None

    # 8) rândurile cu angajați
    rows = []
    month_total_label = month_cell.lower() + ' total'
    for r in reader[8:]:
        first = r[0].strip()
        if first.lower() == month_total_label:
            break
        # oprim parcurgerea cand ajungem la linia absence type key total
        if first.lower() == 'absence type key total':
            break
        if r[0].strip():
            rows.append(r)

    return (
        month, du, year, code_map,
        day_indices, day_numbers,
        total_idx, missing_time_idx,
        rows
    )

def load_into_oracle(records):
    sql = """
    INSERT INTO DIM_RAW_DU_ABSENCES
      (absenceID, month, du, absenceCode, absenceDescription,
       day, year, employeeName, totalMissingDays, missingTime)
    VALUES
      (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
    """
    print("→ [DEBUG] Încep conectarea la Oracle…")
    conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
    print("→ [DEBUG] Conexiune cu DIM_RAW_DU_ABSENCES reuşită, începe executemany()…")
    cur = conn.cursor()
    cur.executemany(sql, records)
    print("→ [DEBUG] executemany() OK, fac commit()…")
    conn.commit()
    print("→ [DEBUG] Commit OK, închid conexiunea.")
    cur.close()
    conn.close()

def main():
    # aflăm de unde pornim cu ID-urile
    next_id = get_start_id()
    print(f"→ Pornim cu absenceID = {next_id}")

    # parse CSV
    (
        month, du, year, code_map,
        day_indices, day_numbers,
        total_idx, missing_time_idx,
        data_rows
    ) = parse_csv(CSV_FILE)

    # pregătim tuplurile
    records = []
    for row in data_rows:
        emp = row[0].strip()
        td = row[total_idx].strip()
        total_days = int(td) if td.isdigit() else None

        # dacă nu avem coloana Missing time, missing_time va fi None
        if missing_time_idx is not None:
            mt = row[missing_time_idx].strip().rstrip('h')
            missing_time = int(mt) if mt.isdigit() else None
        else:
            missing_time = None

        for col_idx, day_num in zip(day_indices, day_numbers):
            code = row[col_idx].strip() or None
            desc = code_map.get(code)
            records.append([
                next_id, month, du, code, desc,
                day_num, year, emp, total_days, missing_time
            ])
            next_id += 1

    print(f"Pregătite {len(records)} înregistrări, de la absenceID inițial până la {next_id-1}.")
    load_into_oracle(records)
    print("Inserție finalizată cu succes.")

if __name__ == '__main__':
    main()
