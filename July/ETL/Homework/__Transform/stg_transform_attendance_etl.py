from dotenv import load_dotenv
import os
import oracledb

# --- Încarcă credențialele din .env ---
load_dotenv()
SRC_USER     = os.getenv("ORACLE_USER_SRC")
SRC_PASSWORD = os.getenv("ORACLE_PASSWORD_SRC")
STG_USER     = os.getenv("ORACLE_USER_STG")
STG_PASSWORD = os.getenv("ORACLE_PASSWORD_STG")
DSN          = os.getenv("ORACLE_DSN")

def get_next_id(cur, table, pk_col, base):
    cur.execute(f"SELECT NVL(MAX({pk_col}),0) FROM {table}")
    (maxid,) = cur.fetchone()
    return maxid + 1 if maxid > 0 else base

def transform_employees_on_training(src_cur, stg_cur):
    # 1) Citește cheile naturale deja existente pentru a evita duplicate
    stg_cur.execute("""
        SELECT sessionName, employeeEmail
          FROM DIM_STG_EMPLOYEES_ON_TRAINING
    """)
    existing_keys = {(row[0], row[1]) for row in stg_cur.fetchall()}

    # 2) Determină next attendanceID în staging
    next_id = get_next_id(stg_cur, "DIM_STG_EMPLOYEES_ON_TRAINING", "attendanceID", 4110)

    # 3) Citește din raw
    src_cur.execute("""
        SELECT sessionName,
               employeeName,
               employeeEmail,
               firstJoin,
               lastLeave,
               inMeeting
          FROM DIM_RAW_TRAINNING_ATTENDANCE
         ORDER BY attendanceID
    """)
    rows = src_cur.fetchall()

    # 4) Filtrează doar rândurile noi și pregătește inserția
    records = []
    for sessionName, employeeName, employeeEmail, firstJoin, lastLeave, inMeeting in rows:
        key = (sessionName, employeeEmail)
        if key in existing_keys:
            continue
        records.append((
            next_id,
            sessionName,
            employeeName,
            employeeEmail,
            firstJoin,
            lastLeave,
            inMeeting
        ))
        existing_keys.add(key)
        next_id += 1

    # 5) Execută inserția
    if records:
        stg_cur.executemany("""
            INSERT INTO DIM_STG_EMPLOYEES_ON_TRAINING
              (attendanceID, sessionName, employeeName, employeeEmail,
               firstJoin, lastLeave, inMeeting)
            VALUES
              (:1, :2, :3, :4, :5, :6, :7)
        """, records)
    print(f"→ Inserate {len(records)} rânduri în DIM_STG_EMPLOYEES_ON_TRAINING")

def transform_training_session(src_cur, stg_cur):
    # 1) Citește sessionName-urile deja existente
    stg_cur.execute("SELECT sessionName FROM DIM_STG_TRAINING_SESSION")
    existing_sessions = {row[0] for row in stg_cur.fetchall()}

    # 2) Determină next trainingID
    next_id = get_next_id(stg_cur, "DIM_STG_TRAINING_SESSION", "trainingID", 5110)

    # 3) Citește DISTINCT din raw
    src_cur.execute("""
        SELECT DISTINCT
               sessionName,
               totalParticipants,
               startTime,
               endTime,
               meetingDuration,
               averageAttendanceTime
          FROM DIM_RAW_TRAINNING_ATTENDANCE
    """)
    rows = src_cur.fetchall()

    # 4) Filtrează numai sesiunile noi și pregătește inserția
    records = []
    for sessionName, totalParticipants, startTime, endTime, meetingDuration, averageAttendanceTime in rows:
        if sessionName in existing_sessions:
            continue
        records.append((
            next_id,
            sessionName,
            totalParticipants,
            startTime,
            endTime,
            meetingDuration,
            averageAttendanceTime
        ))
        existing_sessions.add(sessionName)
        next_id += 1

    # 5) Execută inserția
    if records:
        stg_cur.executemany("""
            INSERT INTO DIM_STG_TRAINING_SESSION
              (trainingID, sessionName, totalParticipants,
               startTime, endTime, meetingDuration, averageAttendanceTime)
            VALUES
              (:1, :2, :3, :4, :5, :6, :7)
        """, records)
    print(f"→ Inserate {len(records)} rânduri în DIM_STG_TRAINING_SESSION")

def main():
    # deschide conexiunile
    src_conn = oracledb.connect(user=SRC_USER,     password=SRC_PASSWORD, dsn=DSN)
    stg_conn = oracledb.connect(user=STG_USER,     password=STG_PASSWORD, dsn=DSN)
    try:
        src_cur = src_conn.cursor()
        stg_cur = stg_conn.cursor()

        transform_employees_on_training(src_cur, stg_cur)
        stg_conn.commit()

        transform_training_session(src_cur, stg_cur)
        stg_conn.commit()
    finally:
        src_cur.close()
        stg_cur.close()
        src_conn.close()
        stg_conn.close()

if __name__ == "__main__":
    main()
