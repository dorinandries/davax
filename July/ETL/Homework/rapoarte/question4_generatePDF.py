from dotenv import load_dotenv
import os
import oracledb
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# ── Load credentials
load_dotenv()
TGT_USER     = os.getenv("ORACLE_USER_TGT")
TGT_PASSWORD = os.getenv("ORACLE_PASSWORD_TGT")
DSN          = os.getenv("ORACLE_DSN")

# Reporting period as datetime objects
PERIOD_START = datetime(2025, 6, 1)
PERIOD_END   = datetime(2025, 8, 31, 0, 0, 0)

# For display purposes only: formatted strings
DISPLAY_START = PERIOD_START.strftime("%d-%b-%y, %H:%M:%S").upper()
DISPLAY_END   = PERIOD_END.strftime("%d-%b-%y, %H:%M:%S").upper()

# Absence codes
OVERTIME_CODE = 'OVT'
VACATION_CODE = 'V'

# PDF layout
title_font_size = 14
text_font_size  = 10
line_height     = 14  # increased for clarity
left_margin     = inch
bullet_indent   = 20  # indent for bullet points


def report_employee_activity():
    # Connect to Oracle
    conn = oracledb.connect(user=TGT_USER, password=TGT_PASSWORD, dsn=DSN)
    cur = conn.cursor()

    try:
        # 1) Map employeeHistoryID -> (name, email)
        cur.execute("""
            SELECT employeeHistoryID, employeeName, employeeEmail
              FROM DIM_TGT_EMPLOYEE_HISTORY
             WHERE isActive = 'Y'
        """)
        eh_map = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

        # 2) Get distinct employees in timesheet in period
        cur.execute("""
            SELECT DISTINCT t.employeeHistoryID
              FROM FACT_TGT_TIMESHEET t
              JOIN DIM_TGT_DATE d ON t.dateID = d.dateID
             WHERE d.fullDate BETWEEN :start_date AND :end_date
        """, start_date=PERIOD_START, end_date=PERIOD_END)
        employees = [r[0] for r in cur.fetchall()]

        # 3) Preload training sessions for absence checks
        cur.execute("""
            SELECT trainingID, sessionName, TRUNC(startTime)
              FROM DIM_TGT_TRAINING_SESSION
        """)
        sessions = cur.fetchall()  # list of (tid, name, session_date)

        # 4) Build report content per employee
        reports = []
        for ehid in employees:
            name, email = eh_map.get(ehid, ('<Unknown>', None))

            # 4a) Total hours
            cur.execute("""
                SELECT NVL(SUM(t.workedHours), 0)
                  FROM FACT_TGT_TIMESHEET t
                  JOIN DIM_TGT_DATE d ON t.dateID = d.dateID
                  JOIN DIM_TGT_ABSENCES a ON t.absenceID = a.absenceID
                 WHERE t.employeeHistoryID = :ehid
                   AND d.fullDate BETWEEN :start_date AND :end_date
                   AND TRIM(a.absenceCode) != :vac 
                   AND TRIM(a.absenceCode) != :ovt
            """, ehid=ehid, start_date=PERIOD_START, end_date=PERIOD_END, vac=VACATION_CODE, ovt=OVERTIME_CODE)
            total_hours = cur.fetchone()[0]

            # 4b) Overtime hours
            cur.execute("""
                SELECT NVL(SUM(t.workedHours), 0)
                  FROM FACT_TGT_TIMESHEET t
                  JOIN DIM_TGT_DATE d ON t.dateID = d.dateID
                  JOIN DIM_TGT_ABSENCES a ON t.absenceID = a.absenceID
                 WHERE t.employeeHistoryID = :ehid
                   AND d.fullDate BETWEEN :start_date AND :end_date
                   AND TRIM(a.absenceCode) = :ovt
            """, ehid=ehid, start_date=PERIOD_START, end_date=PERIOD_END, ovt=OVERTIME_CODE)
            overtime_hours = cur.fetchone()[0]
            # 4c) Vacation hours
            cur.execute("""
                SELECT NVL(SUM(t.workedHours), 0)
                  FROM FACT_TGT_TIMESHEET t
                  JOIN DIM_TGT_DATE d ON t.dateID = d.dateID
                  JOIN DIM_TGT_ABSENCES a ON t.absenceID = a.absenceID
                 WHERE t.employeeHistoryID = :ehid
                   AND d.fullDate BETWEEN :start_date AND :end_date
                   AND TRIM(a.absenceCode) = :vac
            """, ehid=ehid, start_date=PERIOD_START, end_date=PERIOD_END, vac=VACATION_CODE)
            vacation_hours = cur.fetchone()[0]

            # 4d) Trainings attended
            cur.execute("""
                SELECT ts.sessionName
                  FROM FACT_TGT_EMPLOYEES_ON_TRAINING f
                  JOIN DIM_TGT_TRAINING_SESSION ts USING(trainingID)
                 WHERE f.employeeEmail = :email
            """, email=email)
            attended_sessions = [r[0] for r in cur.fetchall()]

            # 4e) Training absences
            missing = []
            for tid, sname, sdate in sessions:
                # find dateID for session
                cur.execute("""
                    SELECT dateID
                      FROM DIM_TGT_DATE
                     WHERE TRUNC(fullDate) = :sdate
                """, sdate=sdate)
                drow = cur.fetchone()
                if not drow:
                    continue
                date_id = drow[0]
                # absence record on that date
                cur.execute("""
                    SELECT a.absenceCode
                      FROM FACT_TGT_DU_ABSENCES f
                      JOIN DIM_TGT_ABSENCES a USING(absenceID)
                     WHERE f.employeeHistoryID = :ehid
                       AND f.dateID = :date_id
                """, ehid=ehid, date_id=date_id)
                for acode, in cur.fetchall():
                    missing.append((sname, acode))

            reports.append({
                'name': name,
                'total_hours': total_hours,
                'overtime_hours': overtime_hours,
                'vacation_hours': vacation_hours,
                'attended_sessions': attended_sessions,
                'missing_trainings': missing
            })

    finally:
        cur.close()
        conn.close()

    # 5) Write to PDF
    c = canvas.Canvas("Employee_Activity_June_2025.pdf", pagesize=letter)
    y = letter[1] - inch
    print(reports)
    for r in reports:
        c.setFont("Helvetica-Bold", title_font_size)
        c.drawString(left_margin, y, r['name'])
        y -= line_height
        c.setFont("Helvetica", text_font_size)
        # use DISPLAY_START and DISPLAY_END for printed period
        c.drawString(left_margin, y, f"A înregistrat în perioada {PERIOD_START} - {PERIOD_END} {r['total_hours']} ore.")
        y -= line_height
        if r['overtime_hours'] > 0:
            c.drawString(left_margin, y, f"A avut ore suplimentare în numar de: {r['overtime_hours']} ore.")
            y -= line_height
        if r['vacation_hours'] > 0:
            c.drawString(left_margin, y, f"A avut concediu în numar de: {r['vacation_hours']} ore.")
            y -= line_height
        if r['attended_sessions']:
            c.drawString(left_margin, y, "A participat la trainingurile:")
            y -= line_height
            for session in r['attended_sessions']:
                c.drawString(left_margin + bullet_indent, y, f"• {session}")
                y -= line_height
        for sname, acode in r['missing_trainings']:
            c.drawString(left_margin, y, f"A lipsit de la trainingul {sname} din motivul că a avut codul {acode}.")
            y -= line_height
        # space between employees
        y -= line_height
        if y < inch:
            c.showPage()
            y = letter[1] - inch

    c.save()
    print("PDF report generated: Employee_Activity_June_2025.pdf")

if __name__ == "__main__":
    report_employee_activity()
