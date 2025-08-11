from dotenv import load_dotenv
import os
import oracledb
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# ── Load credentials ─────────────────────────────────────────────────────────────
load_dotenv()
TGT_USER     = os.getenv("ORACLE_USER_TGT")
TGT_PASSWORD = os.getenv("ORACLE_PASSWORD_TGT")
DSN          = os.getenv("ORACLE_DSN")

# motivated codes = Sick or Vacation (for timesheet)
MOTIVATED = ("S", "V")

def report_missed_training():
    # 1) ask session number and build session name
    num = input("Training session (1/2/3): ").strip()
    session_name = f"Dava.X Academy - ETL Theory training sessions {num}"

    # connect to Oracle
    conn = oracledb.connect(user=TGT_USER, password=TGT_PASSWORD, dsn=DSN)
    cur = conn.cursor()
    try:
        # 2) fetch trainingID + date
        cur.execute(
            """
            SELECT trainingID, TRUNC(startTime)
              FROM DIM_TGT_TRAINING_SESSION
             WHERE sessionName = :sn
            """, sn=session_name
        )
        row = cur.fetchone()
        if not row:
            message = f"No training \u201c{session_name}\u201d found."
            _write_pdf(session_name, [message])
            return

        training_id, session_date = row

        # 3) dateID
        cur.execute(
            """
            SELECT dateID
              FROM DIM_TGT_DATE
             WHERE TRUNC(fullDate) = :d
            """, d=session_date
        )
        row = cur.fetchone()
        if not row:
            message = f"No date entry for {session_date}."
            _write_pdf(session_name, [message])
            return

        date_id = row[0]

        # 4) attended emails
        cur.execute(
            """
            SELECT employeeEmail
              FROM FACT_TGT_EMPLOYEES_ON_TRAINING
             WHERE trainingID = :tid
            """, tid=training_id
        )
        attended = {r[0] for r in cur.fetchall()}

        # 5) map email -> (ehid,name)
        cur.execute(
            """
            SELECT employeeHistoryID, employeeEmail, employeeName
              FROM DIM_TGT_EMPLOYEE_HISTORY
             WHERE isActive = 'Y'
            """
        )
        eh_map = {email: (ehid, name) for ehid, email, name in cur.fetchall()}

        # 6) DU absences (any code)
        cur.execute(
            """
            SELECT f.employeeHistoryID, a.absenceCode, a.absenceDescription
              FROM FACT_TGT_DU_ABSENCES f
              JOIN DIM_TGT_ABSENCES a USING(absenceID)
             WHERE f.projectID = 1
               AND f.dateID    = :did
            """, did=date_id
        )
        du_rows = cur.fetchall()

        # 7) Timesheet absences (only S/V)
        placeholders = ",".join([f":code{i}" for i in range(len(MOTIVATED))])
        sql_ts = f"""
            SELECT t.employeeHistoryID, a.absenceCode, a.absenceDescription
              FROM FACT_TGT_TIMESHEET t
              JOIN DIM_TGT_ABSENCES a USING(absenceID)
             WHERE t.projectID = 1
               AND t.dateID    = :did
               AND a.absenceCode IN ({placeholders})
        """
        params = {"did": date_id}
        for idx, code in enumerate(MOTIVATED):
            params[f"code{idx}"] = code
        cur.execute(sql_ts, params)
        ts_rows = cur.fetchall()

        # 8) aggregate reasons by ehid
        reasons = {}
        for ehid, code, desc in (*du_rows, *ts_rows):
            reasons.setdefault(ehid, []).append((code, desc))

        # 9) build list of missed attendees
        missed = []
        for email, (ehid, name) in eh_map.items():
            if email in attended or ehid not in reasons:
                continue
            for code, desc in reasons[ehid]:
                missed.append((name, code, desc))

        # 10) build report lines
        lines = [f"Training “{session_name}”", ""]
        if not missed:
            lines.append("No employee missed the training")
        else:
            lines.append(f"{'Employee':30}       Code            Reason")
            lines.append("-" * 70)
            for name, code, desc in missed:
                lines.append(f"{name:30}  {code:4}  {desc}")

        # 11) write to PDF
        _write_pdf(session_name, lines)

    finally:
        cur.close()
        conn.close()


def _write_pdf(session_name, lines):
    # sanitize filename
    safe_name = session_name.replace('/', '_')
    filename = f"Who missed the {safe_name} and why.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - inch
    for line in lines:
        c.drawString(inch, y, line)
        y -= 14  # line spacing
        if y < inch:
            c.showPage()
            y = height - inch
    c.save()
    print(f"Report written to {filename}")


if __name__ == "__main__":
    report_missed_training()
