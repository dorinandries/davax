
ALTER SESSION SET NLS_DATE_FORMAT='DD-MON-RR, HH24:MI:SS';

-- ================================================
-- 1) Datele brute din fișierele de prezență per DU
-- ================================================
CREATE TABLE DIM_RAW_DU_ABSENCES(
    absenceID               NUMBER(10) PRIMARY KEY,
    month                   NUMBER(2),
    du                      VARCHAR2(100),
    absenceCode             CHAR(5),
    absenceDescription      VARCHAR2(30),
    day                     NUMBER(2),
    year                    NUMBER(4),
    employeeName            VARCHAR2(100),
    totalMissingDays        NUMBER(5),
    missingTime             NUMBER(5)
) TABLESPACE davax_data;
/*
SELECT DISTINCT absenceCode, absenceDescription
          FROM DIM_RAW_DU_ABSENCES
         WHERE absenceCode IS NOT NULL
           AND absenceDescription IS NOT NULL;
           
SELECT * FROM DIM_RAW_DU_ABSENCES order by absenceid;
SELECT count(*)
          FROM DIM_RAW_DU_ABSENCES
         WHERE absenceCode IS NOT NULL
           AND absenceDescription IS NOT NULL;

delete from DIM_RAW_DU_ABSENCES; commit;

*/

-- ================================================
-- 2) Datele brute din fișierele cu prezența la trainingurile ETL
-- ================================================
CREATE TABLE DIM_RAW_TRAINNING_ATTENDANCE(
    attendanceID            NUMBER(10) PRIMARY KEY,
    sessionName             VARCHAR2(50),
    totalParticipants       Number(10),
    startTime               DATE,
    endTime                 DATE,
    meetingDuration         INTERVAL DAY TO SECOND(0),
    averageAttendanceTime   INTERVAL DAY TO SECOND(0),
    employeeName            VARCHAR2(100),
    firstJoin               DATE,
    lastLeave               DATE,
    inMeeting               INTERVAL DAY TO SECOND(0),
    employeeEmail           VARCHAR2(100),
    participantID           VARCHAR2(100),
    role                    VARCHAR2(50)
) TABLESPACE davax_data;


-- Nu recomand sa se apeleze aceasta instructiune pentru a calcula durata cat a stat un angajat intr-un meeting
-- deoarece diferenta rezultata nu ia in calcul DACA persoanele au si iesit din meeting pe durata de desfasurare
BEGIN
  -- 1) Golesc toate valorile existente din coloana inMeeting pentru a calcula "manual" timpul petrecut de fiecare participant in intalnire
  UPDATE DIM_RAW_TRAINNING_ATTENDANCE
     SET inMeeting = NULL;
  COMMIT;

  -- 2) Recalculez inMeeting din lastLeave - firstJoin - doar ca va fi o diferenta de valori dintre fisier si valorile din tabel.
  UPDATE DIM_RAW_TRAINNING_ATTENDANCE
     SET inMeeting = NUMTODSINTERVAL(lastLeave - firstJoin, 'DAY');
  COMMIT;
END;
/

/*
SELECT * FROM DIM_RAW_TRAINNING_ATTENDANCE order by attendanceID;
SELECT DISTINCT sessionname from DIM_RAW_TRAINNING_ATTENDANCE;

delete from DIM_RAW_TRAINNING_ATTENDANCE where sessionname like '%3'; commit;
*/


      