from dotenv import load_dotenv
import os
import oracledb

# --- Încarcă credențialele din .env ---
load_dotenv()
STG_USER     = os.getenv("ORACLE_USER_STG")
STG_PASSWORD = os.getenv("ORACLE_PASSWORD_STG")
TGT_USER     = os.getenv("ORACLE_USER_TGT")
TGT_PASSWORD = os.getenv("ORACLE_PASSWORD_TGT")
DSN          = os.getenv("ORACLE_DSN")

# Parametri de incremental
BASE_SESSION_ID = 9110
BASE_FACT_ID    = 10110

def get_next_id(cur, table, pk_col, base):
    cur.execute(f"SELECT NVL(MAX({pk_col}), 0) FROM {table}")
    (m,) = cur.fetchone()
    return m + 1 if m > 0 else base

def fetch_stg_sessions(stg_cur):
    stg_cur.execute("""
        SELECT sessionName,
               totalParticipants,
               startTime,
               endTime,
               meetingDuration,
               averageAttendanceTime
          FROM DIM_STG_TRAINING_SESSION
    """)
    return stg_cur.fetchall()

def fetch_existing_tgt_sessions(tgt_cur):
    tgt_cur.execute("""
        SELECT sessionName,
               totalParticipants,
               startTime,
               endTime,
               meetingDuration,
               averageAttendanceTime
          FROM DIM_TGT_TRAINING_SESSION
    """)
    return {tuple(r) for r in tgt_cur.fetchall()}

def insert_tgt_sessions(stg_rows, tgt_cur):
    existing = fetch_existing_tgt_sessions(tgt_cur)
    next_id  = get_next_id(tgt_cur, "DIM_TGT_TRAINING_SESSION", "trainingID", BASE_SESSION_ID)

    records = []
    for sess in stg_rows:
        if sess in existing:
            continue
        sessionName, totalParticipants, startTime, endTime, meetingDuration, averageAttendanceTime = sess
        records.append((
            next_id,
            sessionName,
            totalParticipants,
            startTime,
            endTime,
            meetingDuration,
            averageAttendanceTime
        ))
        existing.add(sess)
        next_id += 1

    if records:
        tgt_cur.executemany("""
            INSERT INTO DIM_TGT_TRAINING_SESSION
              (trainingID,
               sessionName,
               totalParticipants,
               startTime,
               endTime,
               meetingDuration,
               averageAttendanceTime)
            VALUES
              (:1,:2,:3,:4,:5,:6,:7)
        """, records)
    return [r[0] for r in records]

def fetch_stg_employees(stg_cur):
    stg_cur.execute("""
        SELECT attendanceID,
               sessionName,
               employeeEmail,
               firstJoin,
               lastLeave,
               inMeeting
          FROM DIM_STG_EMPLOYEES_ON_TRAINING
    """)
    return stg_cur.fetchall()

def build_session_map(tgt_cur):
    tgt_cur.execute("SELECT trainingID, sessionName FROM DIM_TGT_TRAINING_SESSION")
    return {row[1]: row[0] for row in tgt_cur.fetchall()}

def fetch_existing_fact_emps(tgt_cur):
    tgt_cur.execute("""
        SELECT trainingID,
               employeeEmail,
               firstJoin,
               lastLeave,
               inMeeting
          FROM FACT_TGT_EMPLOYEES_ON_TRAINING
    """)
    return {tuple(r) for r in tgt_cur.fetchall()}

def insert_fact_employees(stg_rows, session_map, tgt_cur):
    existing = fetch_existing_fact_emps(tgt_cur)
    next_id  = get_next_id(tgt_cur, "FACT_TGT_EMPLOYEES_ON_TRAINING", "attendanceID", BASE_FACT_ID)

    records = []
    for _attID, sessionName, email, firstJoin, lastLeave, inMeeting in stg_rows:
        trainingID = session_map.get(sessionName)
        if trainingID is None:
            continue
        key = (trainingID, email, firstJoin, lastLeave, inMeeting)
        if key in existing:
            continue
        records.append((
            next_id,
            trainingID,
            email,
            firstJoin,
            lastLeave,
            inMeeting
        ))
        existing.add(key)
        next_id += 1

    if records:
        tgt_cur.executemany("""
            INSERT INTO FACT_TGT_EMPLOYEES_ON_TRAINING
              (attendanceID,
               trainingID,
               employeeEmail,
               firstJoin,
               lastLeave,
               inMeeting)
            VALUES
              (:1,:2,:3,:4,:5,:6)
        """, records)
    return len(records)

def main():
    # conexiuni
    stg_conn = oracledb.connect(user=STG_USER,    password=STG_PASSWORD, dsn=DSN)
    tgt_conn = oracledb.connect(user=TGT_USER,    password=TGT_PASSWORD, dsn=DSN)
    try:
        stg_cur = stg_conn.cursor()
        tgt_cur = tgt_conn.cursor()

        # 1) Transfer Training Sessions
        stg_sessions   = fetch_stg_sessions(stg_cur)
        new_session_ids = insert_tgt_sessions(stg_sessions, tgt_cur)
        print(f"→ Inserate {len(new_session_ids)} sesiuni în DIM_TGT_TRAINING_SESSION")
        tgt_conn.commit()

        # 2) Transfer Employees on Training
        session_map = build_session_map(tgt_cur)
        stg_emps     = fetch_stg_employees(stg_cur)
        cnt_fact     = insert_fact_employees(stg_emps, session_map, tgt_cur)
        print(f"→ Inserate {cnt_fact} rânduri în FACT_TGT_EMPLOYEES_ON_TRAINING")
        tgt_conn.commit()
    finally:
        stg_cur.close()
        tgt_cur.close()
        stg_conn.close()
        tgt_conn.close()

if __name__ == "__main__":
    main()
