from dotenv import load_dotenv
import os, csv, re
from datetime import datetime, timedelta
import oracledb

# --- Variabilele de conexiune ---
load_dotenv()
USER     = os.getenv("ORACLE_USER_SRC")
PASSWORD = os.getenv("ORACLE_PASSWORD_SRC")
DSN      = os.getenv("ORACLE_DSN")

# Selectează fișierul dorit:
#CSV_FILE = '../etl/Dava.X Academy - ETL Theory training sessions - Attendance report 6-24-25.csv'
#CSV_FILE = '../etl/Dava.X Academy - ETL Theory training sessions - Attendance report 6-25-25.csv'
CSV_FILE = '../etl/Dava.X Academy - ETL Theory training sessions - Attendance report 6-26-25.csv'

ATTENDANCE_ID  = 2110

def get_start_id():
    """Ia MAX(attendanceID)+1 sau ATTENDANCE_ID dacă tabela e goală."""
    conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
    cur  = conn.cursor()
    cur.execute("SELECT NVL(MAX(attendanceID),0) FROM DIM_RAW_TRAINNING_ATTENDANCE")
    (maxid,) = cur.fetchone()
    cur.close()
    conn.close()
    return maxid + 1 if maxid > 0 else ATTENDANCE_ID

def parse_duration(s: str) -> timedelta:
    """
    Parsează un string de forma '1h 59m 6s' într-un timedelta.
    """
    hours = minutes = seconds = 0
    for val, unit in re.findall(r'(\d+)([hms])', s):
        if unit == 'h': hours   = int(val)
        if unit == 'm': minutes = int(val)
        if unit == 's': seconds = int(val)
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)

def parse_csv(path):
    # Deschidem cu encoding UTF-16 și delimiter tab
    with open(path, encoding='utf-16', newline='') as f:
        reader = list(csv.reader(f, delimiter='\t'))

    # 1) sessionName       → linia 2, col2
    sessionName = reader[1][1].strip()

    # 2) totalParticipants → linia 3, col2
    totalParticipants = int(reader[2][1].strip())

    # 3) startTime         → linia 4, col2 (ex: "6/24/25, 1:47:45 PM")
    startTime = datetime.strptime(reader[3][1].strip(), "%m/%d/%y, %I:%M:%S %p")

    # 4) endTime           → linia 5, col2
    endTime   = datetime.strptime(reader[4][1].strip(), "%m/%d/%y, %I:%M:%S %p")

    # 5) meetingDuration   → linia 6, col2 ("1h 59m 6s")
    meetingDuration = parse_duration(reader[5][1].strip())

    # 6) averageAttendanceTime → linia 7, col2
    averageAttendanceTime = parse_duration(reader[6][1].strip())

    # 7) sărim liniile 8–10 și parcurgem participanții de la linia 11
    participants = []
    for row in reader[10:]:
        name = row[0].strip()
        if name == "3. In-Meeting Activities":
            break
        if not name:
            continue

        firstJoin = datetime.strptime(row[1].strip(), "%m/%d/%y, %I:%M:%S %p")
        lastLeave = datetime.strptime(row[2].strip(), "%m/%d/%y, %I:%M:%S %p")
        inMeeting = parse_duration(row[3].strip())
        email     = row[4].strip()
        partID    = row[5].strip()
        role      = row[6].strip()

        participants.append((name, firstJoin, lastLeave, inMeeting, email, partID, role))

    return (sessionName, totalParticipants, startTime, endTime,
            meetingDuration, averageAttendanceTime, participants)

def load_into_oracle(records):
    print("→ [DEBUG] Încep conectarea la Oracle…")
    conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
    print("→ [DEBUG] Conexiune cu DIM_RAW_TRAINNING_ATTENDANCE reuşită, începe executemany()…")
    cur = conn.cursor()

    cur.execute("ALTER SESSION SET NLS_DATE_FORMAT='DD-MON-RR, HH24:MI:SS'")
    sql = """
    INSERT INTO DIM_RAW_TRAINNING_ATTENDANCE
      (attendanceID, sessionName, totalParticipants,
       startTime, endTime, meetingDuration,
       averageAttendanceTime, employeeName,
       firstJoin, lastLeave, inMeeting,
       employeeEmail, participantID, role)
    VALUES
      (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12, :13, :14)
    """
    cur.executemany(sql, records)
    print("→ [DEBUG] executemany() OK, fac commit()…")
    conn.commit()
    print("→ [DEBUG] Commit OK, închid conexiunea.")
    cur.close()
    conn.close()

def main():
    next_id = get_start_id()
    print(f"→ Vom începe cu attendanceID = {next_id}")

    (sessionName, totalParticipants, startTime, endTime,
     meetingDuration, averageAttendanceTime, participants) = parse_csv(CSV_FILE)

    # Pregătim lista de tupluri pentru executemany()
    records = []
    for (name, firstJoin, lastLeave, inMeeting, email, partID, role) in participants:
        records.append([
            next_id,
            sessionName,
            totalParticipants,
            startTime,
            endTime,
            meetingDuration,
            averageAttendanceTime,
            name,
            firstJoin,
            lastLeave,
            inMeeting,
            email,
            partID,
            role
        ])
        next_id += 1

    print(f"Pregătite {len(records)} înregistrări, de la attendanceID inițial până la {next_id-1}.")
    load_into_oracle(records)
    print("Inserție finalizată cu succes.")
    print(f"  IDs: {next_id-len(records)} – {next_id-1}")

if __name__ == "__main__":
    main()
