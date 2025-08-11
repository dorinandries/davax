from dotenv import load_dotenv
import os
import oracledb
import matplotlib.pyplot as plt

# ── Load credentials ─────────────────────────────────────────────────────────────
load_dotenv()
TGT_USER     = os.getenv("ORACLE_USER_TGT")
TGT_PASSWORD = os.getenv("ORACLE_PASSWORD_TGT")
DSN          = os.getenv("ORACLE_DSN")

def plot_absence_counts():
    # 1) Connect
    conn = oracledb.connect(user=TGT_USER, password=TGT_PASSWORD, dsn=DSN)
    cur = conn.cursor()

    try:
        # 2) Query: count distinct employees per absenceCode
        cur.execute("""
            SELECT 
              a.absenceCode,
              COUNT(DISTINCT f.employeeHistoryID) AS cnt
            FROM FACT_TGT_DU_ABSENCES f
            JOIN DIM_TGT_ABSENCES    a USING(absenceID)
            GROUP BY a.absenceCode
            ORDER BY a.absenceCode
        """)
        data = cur.fetchall()  # list of (code, cnt)

    finally:
        cur.close()
        conn.close()

    # 3) Unpack for plotting
    codes, counts = zip(*data) if data else ([], [])

    # 4) Plot
    plt.figure()
    plt.bar(codes, counts)
    plt.xlabel("Cod absente")
    plt.ylabel("Numar de persoane")
    plt.title("Numarul de persoane in raport cu tipul de absente")
    plt.tight_layout()

    # 5) Save as PDF
    plt.savefig("Raport_Grafic_Numar_Absente.pdf")
    plt.close()
    print("Saved chart to Raport_Grafic_Numar_Absente..pdf")

if __name__ == "__main__":
    plot_absence_counts()