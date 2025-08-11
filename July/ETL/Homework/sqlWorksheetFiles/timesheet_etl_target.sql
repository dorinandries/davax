

-- run this first
ALTER SESSION SET NLS_DATE_FORMAT='DD-MON-RR, HH24:MI:SS';


-- ================================================
-- 1) Tabel pentru angajati
-- ================================================
CREATE TABLE FACT_TGT_EMPLOYEE (
  employeeID       NUMBER(10)        PRIMARY KEY,
  employeeName     VARCHAR2(100),
  employeeEmail    VARCHAR2(100),
  grade            VARCHAR2(50),
  disciplineName   VARCHAR2(100),
  lineManager      VARCHAR2(100),
  du               VARCHAR2(100)
) TABLESPACE davax_data;

--Comanda pentru SCD2
UPDATE FACT_TGT_EMPLOYEE
   SET grade = 'ST'
 WHERE employeeID = 7110
   AND grade      = 'DT';

COMMIT;

/*

select * from FACT_TGT_EMPLOYEE;

delete from DIM_TGT_EMPLOYEE_HISTORY; commit;
delete from FACT_TGT_EMPLOYEE; commit;
*/

-- ================================================
-- 2) SCD2 history table la angajati
-- ================================================
CREATE TABLE DIM_TGT_EMPLOYEE_HISTORY (
  employeeHistoryID  NUMBER(10)       PRIMARY KEY,
  employeeID         NUMBER(10)       CONSTRAINT fk_dim_emp_hist_emp   REFERENCES FACT_TGT_EMPLOYEE(employeeID),
  employeeName       VARCHAR2(100),
  employeeEmail      VARCHAR2(100),
  grade              VARCHAR2(50),
  disciplineName     VARCHAR2(100),
  lineManager        VARCHAR2(100),
  du                 VARCHAR2(100),
  startDate          DATE,
  endDate            DATE,
  isActive           CHAR(1) DEFAULT 'N'
) TABLESPACE davax_data;

/*

select * from DIM_TGT_EMPLOYEE_HISTORY;

delete from DIM_TGT_EMPLOYEE_HISTORY; commit;

*/

-- Sequence pentru generarea cheilor surrogate în DIM_TGT_EMPLOYEE_HISTORY
CREATE SEQUENCE EMPLOYEE_HIST_SEQ
  START WITH 1
  INCREMENT BY 1
  NOCACHE
  NOCYCLE;
/

-- Trigger pentru popularea SCD2 în DIM_TGT_EMPLOYEE_HISTORY
CREATE OR REPLACE TRIGGER trg_sync_emp_history
AFTER INSERT OR UPDATE
  ON FACT_TGT_EMPLOYEE
FOR EACH ROW
DECLARE
  -- variabile pentru valorile curente din history
  v_old_name        DIM_TGT_EMPLOYEE_HISTORY.employeeName%TYPE;
  v_old_email       DIM_TGT_EMPLOYEE_HISTORY.employeeEmail%TYPE;
  v_old_grade       DIM_TGT_EMPLOYEE_HISTORY.grade%TYPE;
  v_old_discipline  DIM_TGT_EMPLOYEE_HISTORY.disciplineName%TYPE;
  v_old_manager     DIM_TGT_EMPLOYEE_HISTORY.lineManager%TYPE;
  v_old_du          DIM_TGT_EMPLOYEE_HISTORY.du%TYPE;
  v_cnt             NUMBER;
BEGIN
  -- 1) Căutăm dacă există deja o versiune activă pentru acest employeeID
  SELECT COUNT(*)
    INTO v_cnt
    FROM DIM_TGT_EMPLOYEE_HISTORY
   WHERE employeeID = :NEW.employeeID
     AND isActive   = 'Y';

  IF v_cnt = 0 THEN
    -- Nu există niciun istoric activ: inserăm prima versiune
    INSERT INTO DIM_TGT_EMPLOYEE_HISTORY (
      employeeHistoryID,
      employeeID,
      employeeName,
      employeeEmail,
      grade,
      disciplineName,
      lineManager,
      du,
      startDate,
      endDate,
      isActive
    ) VALUES (
      EMPLOYEE_HIST_SEQ.NEXTVAL,
      :NEW.employeeID,
      :NEW.employeeName,
      :NEW.employeeEmail,
      :NEW.grade,
      :NEW.disciplineName,
      :NEW.lineManager,
      :NEW.du,
      SYSDATE,
      NULL,       -- NULL semnalează „până în prezent”
      'Y'
    );

  ELSE
    -- Există deja o versiune activă: preluăm valorile curente
    SELECT
      employeeName,
      employeeEmail,
      grade,
      disciplineName,
      lineManager,
      du
      INTO
        v_old_name,
        v_old_email,
        v_old_grade,
        v_old_discipline,
        v_old_manager,
        v_old_du
    FROM DIM_TGT_EMPLOYEE_HISTORY
    WHERE employeeID = :NEW.employeeID
      AND isActive   = 'Y';

    -- 2) Verificăm dacă cel puțin un câmp s-a schimbat
    IF NVL(v_old_name,       '§') <> NVL(:NEW.employeeName,    '§')
    OR   NVL(v_old_email,      '§') <> NVL(:NEW.employeeEmail,   '§')
    OR   NVL(v_old_grade,      '§') <> NVL(:NEW.grade,           '§')
    OR   NVL(v_old_discipline, '§') <> NVL(:NEW.disciplineName,  '§')
    OR   NVL(v_old_manager,    '§') <> NVL(:NEW.lineManager,     '§')
    OR   NVL(v_old_du,         '§') <> NVL(:NEW.du,               '§')
    THEN
      -- 3) „Încidem” versiunea curentă
      UPDATE DIM_TGT_EMPLOYEE_HISTORY
         SET endDate  = SYSDATE,
             isActive = 'N'
       WHERE employeeID = :NEW.employeeID
         AND isActive   = 'Y';

      -- 4) Cream o nouă versiune cu valorile din FACT_TGT_EMPLOYEE
      INSERT INTO DIM_TGT_EMPLOYEE_HISTORY (
        employeeHistoryID,
        employeeID,
        employeeName,
        employeeEmail,
        grade,
        disciplineName,
        lineManager,
        du,
        startDate,
        endDate,
        isActive
      ) VALUES (
        EMPLOYEE_HIST_SEQ.NEXTVAL,
        :NEW.employeeID,
        :NEW.employeeName,
        :NEW.employeeEmail,
        :NEW.grade,
        :NEW.disciplineName,
        :NEW.lineManager,
        :NEW.du,
        SYSDATE,
        NULL,
        'Y'
      );
    END IF;
  END IF;
END;
/


-- ================================================
-- 3) Tabel pentru zile
-- ================================================
CREATE TABLE DIM_TGT_DATE (
  dateID      NUMBER(10) PRIMARY KEY,
  fullDate    DATE NOT NULL,
  day         NUMBER(2),
  month       NUMBER(2),
  year        NUMBER(4),
  dayOfWeek   VARCHAR2(15),
  isWeekend   CHAR(1) DEFAULT 'N'
) TABLESPACE davax_data;

/*

select * from DIM_TGT_DATE;

delete from DIM_TGT_DATE; commit;
*/

-- ================================================
-- 4) DIM_TGT_PROJECT
-- ================================================
CREATE TABLE DIM_TGT_PROJECT (
  projectID           NUMBER(10) PRIMARY KEY,
  projectDescription  VARCHAR2(100)
) TABLESPACE davax_data;

/*

select * from DIM_TGT_PROJECT;

*/


-- ================================================
-- 5) DIM_TGT_ABSENCES
-- ================================================
CREATE TABLE DIM_TGT_ABSENCES (
  absenceID           NUMBER(10) PRIMARY KEY,
  absenceCode         VARCHAR2(10),
  absenceDescription  VARCHAR2(100)
) TABLESPACE davax_data;

/*

select * from DIM_TGT_ABSENCES;

*/



-- ================================================
-- 6) DIM_TGT_TRAINING_SESSION
-- ================================================
CREATE TABLE DIM_TGT_TRAINING_SESSION (
  trainingID             NUMBER(10)  PRIMARY KEY,
  sessionName            VARCHAR2(50),
  totalParticipants      NUMBER(10),
  startTime              DATE,
  endTime                DATE,
  meetingDuration        INTERVAL DAY(2) TO SECOND(0),
  averageAttendanceTime  INTERVAL DAY(2) TO SECOND(0)
) TABLESPACE davax_data;

/*

select * from DIM_TGT_TRAINING_SESSION;

*/

-- ================================================
-- 7) FACT_TGT_EMPLOYEES_ON_TRAINING
-- ================================================
CREATE TABLE FACT_TGT_EMPLOYEES_ON_TRAINING (
  attendanceID    NUMBER(10)          PRIMARY KEY,
  trainingID      NUMBER(10)          CONSTRAINT fk_fact_eot_sess   REFERENCES DIM_TGT_TRAINING_SESSION(trainingID),
  employeeEmail   VARCHAR2(100),
  firstJoin       DATE,
  lastLeave       DATE,
  inMeeting       INTERVAL DAY(2) TO SECOND(0)
) TABLESPACE davax_data;

/*

select * from FACT_TGT_EMPLOYEES_ON_TRAINING;

*/

-- ================================================
-- 8) FACT_TGT_DU_ABSENCES
-- ================================================
CREATE TABLE FACT_TGT_DU_ABSENCES (
  duAbsenceID         NUMBER(10)     PRIMARY KEY,
  employeeHistoryID   NUMBER(10)     CONSTRAINT fk_fact_du_ehist   REFERENCES DIM_TGT_EMPLOYEE_HISTORY(employeeHistoryID),
  absenceID           NUMBER(10)     CONSTRAINT fk_fact_du_absence REFERENCES DIM_TGT_ABSENCES(absenceID),
  dateID              NUMBER(10)     CONSTRAINT fk_fact_du_date    REFERENCES DIM_TGT_DATE(dateID),
  projectID           NUMBER(10)     CONSTRAINT fk_fact_du_project REFERENCES DIM_TGT_PROJECT(projectID),
  du                  VARCHAR2(100)
) TABLESPACE davax_data;

/*

SELECT * FROM FACT_TGT_DU_ABSENCES;

SELECT
  f.duAbsenceID,
  eh.employeeName                  AS "Angajat",
  a.absenceCode || ' – ' ||
    a.absenceDescription           AS "Absenta",
  TO_CHAR(d.fullDate, 'DD-MON-YYYY')||', '||
    TO_CHAR(d.fullDate, 'HH24:MI:SS') AS "Data si ora",
  p.projectDescription             AS "Proiect",
  f.du                             AS "DU"
FROM FACT_TGT_DU_ABSENCES f
  JOIN DIM_TGT_EMPLOYEE_HISTORY eh
    ON f.employeeHistoryID = eh.employeeHistoryID
  JOIN DIM_TGT_ABSENCES a
    ON f.absenceID = a.absenceID
  JOIN DIM_TGT_DATE d
    ON f.dateID = d.dateID
  JOIN DIM_TGT_PROJECT p
    ON f.projectID = p.projectID
--where eh.employeeName like '%Andries%'
ORDER BY f.duAbsenceID;

delete from FACT_TGT_DU_ABSENCES; commit;

*/


-- ================================================
-- 9) FACT_TGT_TIMESHEET
-- ================================================
CREATE TABLE FACT_TGT_TIMESHEET (
  timesheetID         NUMBER(10)     PRIMARY KEY,
  employeeHistoryID   NUMBER(10)     CONSTRAINT fk_ts_ehist       REFERENCES DIM_TGT_EMPLOYEE_HISTORY(employeeHistoryID),
  dateID              NUMBER(10)     CONSTRAINT fk_ts_date        REFERENCES DIM_TGT_DATE(dateID),
  absenceID           NUMBER(10)     CONSTRAINT fk_ts_absence     REFERENCES DIM_TGT_ABSENCES(absenceID),
  projectID           NUMBER(10)     CONSTRAINT fk_ts_project     REFERENCES DIM_TGT_PROJECT(projectID),
  workedHours         NUMBER(10,2)
) TABLESPACE davax_data;

/*

// insert Vacation record
insert into FACT_TGT_TIMESHEET (timesheetid, employeehistoryid, dateid, absenceid, projectid, workedhours) VALUES (21130, 8110, 93, 8, 1, 8);
insert into FACT_TGT_TIMESHEET (timesheetid, employeehistoryid, dateid, absenceid, projectid, workedhours) VALUES (21131, 8110, 96, 8, 1, 8);
insert into FACT_TGT_TIMESHEET (timesheetid, employeehistoryid, dateid, absenceid, projectid, workedhours) VALUES (21132, 8110, 97, 8, 1, 8);

// insert Overtime record
insert into FACT_TGT_TIMESHEET (timesheetid, employeehistoryid, dateid, absenceid, projectid, workedhours) VALUES (21133, 8111, 93, 8, 1, 3);
insert into FACT_TGT_TIMESHEET (timesheetid, employeehistoryid, dateid, absenceid, projectid, workedhours) VALUES (21134, 8111, 96, 8, 1, 5);
insert into FACT_TGT_TIMESHEET (timesheetid, employeehistoryid, dateid, absenceid, projectid, workedhours) VALUES (21135, 8111, 97, 8, 1, 1);

delete from FACT_TGT_TIMESHEET; commit;

SELECT NVL(SUM(t.workedHours), 0)
                  FROM FACT_TGT_TIMESHEET t
                  JOIN DIM_TGT_DATE d ON t.dateID = d.dateID
                  JOIN DIM_TGT_ABSENCES a ON t.absenceID = a.absenceID
                 WHERE t.employeeHistoryID = 8111
                   AND d.fullDate BETWEEN '01-JUN-25, 00:00:00' AND '31-AUG-25, 00:00:00'
                   AND TRIM(a.absenceCode) = 'OVT';
*/