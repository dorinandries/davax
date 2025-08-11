

-- run this first
ALTER SESSION SET NLS_DATE_FORMAT='DD-MON-RR, HH24:MI:SS';



-- ================================================
-- 1) Codurile de absență bazate normalizarea datelor din fișierele cu prezența per DU
-- ================================================

CREATE TABLE DIM_STG_DU_ABSENCE_CODES (
    absenceCodeID        NUMBER(10) PRIMARY KEY,
    absenceCode          VARCHAR2(5),
    absenceDescription   VARCHAR2(50)
) TABLESPACE davax_data;


/*

select * from DIM_STG_DU_ABSENCE_CODES order by absenceCodeID ;

delete from DIM_STG_DU_ABSENCE_CODES; commit;

*/


-- ================================================
-- 2) Absențele propriu-zise, legate prin FK la coduri bazate normalizarea datelor din fișierele cu prezența per DU
-- ================================================
CREATE TABLE DIM_STG_DU_ABSENCES (
    absenceID            NUMBER(10) PRIMARY KEY,
    employeeName         VARCHAR2(100),
    absenceCodeID        NUMBER(10),
    absenceDate          DATE,
    du                   VARCHAR2(100),
    CONSTRAINT fk_du_absences_to_codes
      FOREIGN KEY (absenceCodeID)
      REFERENCES DIM_STG_DU_ABSENCE_CODES(absenceCodeID)
) TABLESPACE davax_data;

/*

SELECT 
    d.absenceID, d.employeeName,
    c.absenceCode,
    d.absenceDate, d.du
FROM 
    DIM_STG_DU_ABSENCES d
    JOIN DIM_STG_DU_ABSENCE_CODES c
      ON d.absenceCodeID = c.absenceCodeID
    --where employeename like '%Andries%'
ORDER BY 
    d.du desc, d.absenceDate, d.employeename;

delete from DIM_STG_DU_ABSENCES; commit;

SELECT DISTINCT employeeName, du
          FROM DIM_STG_DU_ABSENCES;


*/



-- ================================================
-- 3) Prezența in meetinguri bazate normalizarea datelor din fișierele cu prezența la curs
-- ================================================
CREATE TABLE DIM_STG_EMPLOYEES_ON_TRAINING (
    attendanceID     NUMBER(10)        PRIMARY KEY,
    sessionName      VARCHAR2(50),
    employeeName     VARCHAR2(100),
    employeeEmail    VARCHAR2(100),
    firstJoin        DATE,
    lastLeave        DATE,
    inMeeting        INTERVAL DAY TO SECOND(0)
) TABLESPACE davax_data;

/*
select * from DIM_STG_EMPLOYEES_ON_TRAINING order by attendanceID ;

SELECT employeeName, employeeEmail
          FROM DIM_STG_EMPLOYEES_ON_TRAINING;
          SELECT DISTINCT employeeName, du
          FROM DIM_STG_DU_ABSENCES;
delete from DIM_STG_EMPLOYEES_ON_TRAINING; commit;

*/


-- ================================================
-- 4) Trainingurile care au avut loc bazate normalizarea datelor din fișierele cu prezența la curs
-- ================================================
CREATE TABLE DIM_STG_TRAINING_SESSION (
    trainingID            NUMBER(10)   PRIMARY KEY,
    sessionName           VARCHAR2(50),
    totalParticipants     NUMBER(10),
    startTime             DATE,
    endTime               DATE,
    meetingDuration       INTERVAL DAY TO SECOND(0),
    averageAttendanceTime INTERVAL DAY TO SECOND(0)
) TABLESPACE davax_data;


/*
select * from DIM_STG_TRAINING_SESSION order by trainingID ;

delete from DIM_STG_TRAINING_SESSION; commit;

*/


-- ================================================
-- 5) Tabel pentru angajati
-- ================================================
CREATE TABLE DIM_STG_EMPLOYEE (
  employeeID       NUMBER(10)        PRIMARY KEY,
  employeeName     VARCHAR2(100),
  employeeEmail    VARCHAR2(100),
  grade            VARCHAR2(50),
  disciplineName   VARCHAR2(100),
  lineManager      VARCHAR2(100),
  du               VARCHAR2(100)
) TABLESPACE davax_data;


/*
select * from DIM_STG_EMPLOYEE;

delete from DIM_STG_EMPLOYEE; commit;
*/

