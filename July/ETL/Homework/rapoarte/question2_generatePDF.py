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

# Prompt and build session name, then generate a PDF with session details
def report_training_summary():
    num = input("Training session (1/2/3): ").strip()
    session_name = f"Dava.X Academy - ETL Theory training sessions {num}"

    # Connect to Oracle
    conn = oracledb.connect(user=TGT_USER, password=TGT_PASSWORD, dsn=DSN)
    cur = conn.cursor()

    try:
        # Fetch session details
        cur.execute(
            """
            SELECT trainingID, startTime, endTime, meetingDuration
              FROM DIM_TGT_TRAINING_SESSION
             WHERE sessionName = :sn
            """, sn=session_name
        )
        row = cur.fetchone()
        if not row:
            print(f"No training “{session_name}” found.")
            return

        training_id, start_dt, end_dt, duration = row

        # Count participants
        cur.execute(
            """
            SELECT COUNT(*)
              FROM FACT_TGT_EMPLOYEES_ON_TRAINING
             WHERE trainingID = :tid
            """, tid=training_id
        )
        total_participants = cur.fetchone()[0]

        # Format date and times
        date_str = start_dt.strftime("%d-%b-%y").upper()
        start_time = start_dt.strftime("%H:%M:%S")
        end_time = end_dt.strftime("%H:%M:%S")

        # Prepare lines for PDF
        lines = [
            f"                            ~ {session_name} ~",
            "",
            f"Data: {date_str}",
            f"Inceput la ora: {start_time}",
            f"Finalizat la ora: {end_time}",
            f"Numar participanti: {total_participants}",
            f"Durata: {duration}"
        ]

        # Generate PDF
        _write_pdf(session_name, lines)

    finally:
        cur.close()
        conn.close()


def _write_pdf(session_name, lines):
    # Sanitize filename by replacing slashes
    safe_name = session_name.replace("/", "_")
    filename = f"Details about {safe_name}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - inch
    for line in lines:
        c.drawString(inch, y, line)
        y -= 14
        if y < inch:
            c.showPage()
            y = height - inch
    c.save()
    print(f"PDF report written to {filename}")


if __name__ == "__main__":
    report_training_summary()
