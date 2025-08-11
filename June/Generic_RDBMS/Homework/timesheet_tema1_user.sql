
/*
-- Drop tables if needed

drop table time_types;
drop table timesheets;
drop table Employees_Projects;
drop table employees;
drop table employments;
drop table offices;
drop table projects;
drop table countries;
drop table programs;
drop table departments;
drop table jobs;

*/
-- 1. -------------- Tables without FK --------------

-- JOBS: lookup of job titles eg: IT, HR etc
CREATE TABLE Jobs (
  job_id    VARCHAR2(10)   PRIMARY KEY,
  name      VARCHAR2(35)   NOT NULL
) TABLESPACE davax_data;

-- DEPARTMENTS: lookup of organizational units
CREATE TABLE Departments (
  department_id  NUMBER(6,0)   PRIMARY KEY,
  name           VARCHAR2(30)  NOT NULL
) TABLESPACE davax_data;

-- PROGRAM: lookup of employment programs
CREATE TABLE Programs (
  program_id    VARCHAR2(10)   PRIMARY KEY,
  name          VARCHAR2(20)   NOT NULL,
  daily_hours   NUMBER(1,0)    NOT NULL
) TABLESPACE davax_data;

-- COUNTRY: list of countries
CREATE TABLE Countries (
  country_id  CHAR(2)         PRIMARY KEY,
  name        VARCHAR2(60)    NOT NULL
) TABLESPACE davax_data;

CREATE TABLE Projects (
  project_id   VARCHAR2(15)   PRIMARY KEY,
  name         VARCHAR2(50)   NOT NULL,
  activ        CHAR(1)        DEFAULT 'Y'
                  CHECK (activ IN ('Y','N')),
  details      CLOB           -- can store JSON
) TABLESPACE davax_data;

ALTER TABLE Projects
ADD CONSTRAINT chk_details_is_json
CHECK (details IS JSON);


CREATE TABLE Time_Types (
  time_type_id  VARCHAR2(10)   PRIMARY KEY,
  name          VARCHAR2(30)   NOT NULL
) TABLESPACE davax_data;


-- 2. -------------- Tables with FK --------------

-- OFFICES: each office belongs to a country
CREATE TABLE Offices (
  office_id       VARCHAR2(10)   PRIMARY KEY,
  country_id      CHAR(2)        NOT NULL,
  city_name       VARCHAR2(30)   NOT NULL,
  postal_code     VARCHAR2(13)   NOT NULL,
  street_address  VARCHAR2(40)   NOT NULL,
  CONSTRAINT fk_offices_country FOREIGN KEY(country_id)
    REFERENCES Countries(country_id)
) TABLESPACE davax_data;

-- EMPLOYMENT: employment types linked to program
CREATE TABLE Employments (
  employment_id  VARCHAR2(10)   PRIMARY KEY,
  name           VARCHAR2(30)   NOT NULL,
  program_id     VARCHAR2(10)   NOT NULL,
  CONSTRAINT fk_employment_program FOREIGN KEY(program_id)
    REFERENCES Programs(program_id)
) TABLESPACE davax_data;


-- 3. -------------- Core entity: EMPLOYEES --------------

CREATE TABLE Employees (
  employee_id     NUMBER(6)       PRIMARY KEY,
  first_name      VARCHAR2(20)    NOT NULL,
  last_name       VARCHAR2(20)    NOT NULL,
  email           VARCHAR2(30)    NOT NULL,
  phone_number    VARCHAR2(20),
  hire_date       DATE            NOT NULL,
  job_id          VARCHAR2(10)    NOT NULL,
  department_id   NUMBER(6)       NOT NULL,
  employment_id   VARCHAR2(10)    NOT NULL,
  office_id       VARCHAR2(10)    NOT NULL,
  CONSTRAINT uq_employees_email UNIQUE(email),
  CONSTRAINT fk_employees_job     FOREIGN KEY(job_id)
    REFERENCES Jobs(job_id),
  CONSTRAINT fk_employees_dept    FOREIGN KEY(department_id)
    REFERENCES Departments(department_id),
  CONSTRAINT fk_employees_empmt   FOREIGN KEY(employment_id)
    REFERENCES Employments(employment_id),
  CONSTRAINT fk_employees_office  FOREIGN KEY(office_id)
    REFERENCES Offices(office_id)
) TABLESPACE davax_data;

-- 4. -------------- Join table --------------

CREATE TABLE Employees_Projects (
  employee_project_id  VARCHAR2(22)   PRIMARY KEY,
  project_id           VARCHAR2(15)   NOT NULL,
  employee_id          NUMBER(6)      NOT NULL,
  CONSTRAINT fk_ep_proj      FOREIGN KEY(project_id)
    REFERENCES Projects(project_id),
  CONSTRAINT fk_ep_employee  FOREIGN KEY(employee_id)
    REFERENCES Employees(employee_id)
) TABLESPACE davax_data;



-- 5. -------------- TIMESHEET fact table --------------

CREATE TABLE Timesheets (
  timesheet_id         NUMBER(20)     PRIMARY KEY,
  employee_project_id  VARCHAR2(22)   NOT NULL,
  time_type_id         VARCHAR2(10)   NOT NULL,
  day_of_work          DATE           NOT NULL,
  hours_per_day        NUMBER(1,0),
  CONSTRAINT fk_ts_ep      FOREIGN KEY(employee_project_id)
    REFERENCES Employees_Projects(employee_project_id),
  CONSTRAINT fk_ts_tt      FOREIGN KEY(time_type_id)
    REFERENCES Time_Types(time_type_id)
) TABLESPACE davax_data;

CREATE OR REPLACE TRIGGER trg_check_data_timesheet
  BEFORE INSERT OR UPDATE ON Timesheets
  FOR EACH ROW
BEGIN
  IF :NEW.day_of_work < TRUNC(SYSDATE) - 7
     OR :NEW.day_of_work > TRUNC(SYSDATE) THEN
    RAISE_APPLICATION_ERROR(
      -20001,
      'The day of work must be between today and the past 7 days'
    );
  END IF;
END;
/

-- 6. -------------- Indexes on all FKs (PKs implicitly indexed) --------------

-- Employees FKs
CREATE INDEX idx_emp_office    ON Employees(office_id)     TABLESPACE davax_index;
CREATE INDEX idx_emp_proj_fk   ON Employees(project_id)    TABLESPACE davax_index;

-- Employee_Projects FKs
CREATE INDEX idx_ep_proj       ON Employees_Projects(project_id)  TABLESPACE davax_index;
CREATE INDEX idx_ep_employee   ON Employees_Projects(employee_id) TABLESPACE davax_index;

-- Offices FK
CREATE INDEX idx_off_country   ON Offices(country_id)       TABLESPACE davax_index;

-- Timesheet FKs
CREATE INDEX idx_ts_ep         ON Timesheets(employee_project_id) TABLESPACE davax_index;
CREATE INDEX idx_ts_tt         ON Timesheets(time_type_id)       TABLESPACE davax_index;

-- 7. -------------- Indexes on other columns --------------

/*
Legend:
index name will be as: idx_[table name]_[column(s)]
*/
--  Why: users will frequently query timesheet rows by date range (e.g. “show me all entries from this week”).
--  Use case: reports, dashboards or filters that ask for all hours logged between two dates.

CREATE INDEX idx_ts_day_of_work
  ON Timesheets(day_of_work)
  TABLESPACE davax_index;


-- Why: many filters start by employee‐project then restrict to a date range.
-- Use case: this index allows the view of an individual employee’s timesheet history to fetch only that employee’s rows in date order.
-- Use case: view showing employee’s history:
--   select … from Timesheet 
--    WHERE employee_project_id = :epid
--      AND entry_date BETWEEN :d1 AND :d2;
CREATE INDEX idx_ts_ep_date
  ON Timesheets(employee_project_id, day_of_work)
  TABLESPACE davax_index;
  
--  Why: a composite index on (employee_project_id, time_type_id, entry_date) matches the exact filter pattern of “which hours did a given employee-project log for a specific time type over a date range.”
--  Possible use case: a dashboard where someone selects an employee on Project X and wants to see how many “Overtime” hours they logged each day over the last month.
-- Possible use case (not tested )
--   select * from Timesheets
--    WHERE employee_project_id = :epid
--      AND time_type_id = :ttid
--      AND entry_date BETWEEN :d1 AND :d2;
CREATE INDEX idx_ts_ep_tt_date
  ON Timesheets(employee_project_id, time_type_id, day_of_work)
  TABLESPACE davax_index;
  
-- Why: your view and joins need to find which projects each employee has been assigned.
  
CREATE INDEX idx_ep_emp_proj
  ON Employees_Projects(employee_id, project_id)
  TABLESPACE davax_index;


-- 8. -------------- Insert countries --------------
/*
* this table contains the countries from Europe
* use the script from folder Inserts / Countries_insert.txt
*/
@Inserts/Countries_inserts.txt
-- select * from countries;

-- 9. -------------- Insert Offices --------------
/*
* this table contains the informations about each office all around the world
* use the script from folder Inserts/Offices_insert.txt
*/
@Inserts/Offices_insert.txt
-- select * from offices;

-- 10. -------------- Insert Programs --------------
/*
* this table contains types of employment working hours
eg: full time 8 hours; full time 7 hours; part-time 6 hours; part-time 4 hours; etc
* use the script from folder Inserts/Programs_insert.txt
*/
@Inserts/Programs_insert.txt
--select * from Programs;

-- 11. -------------- Insert Employments --------------
/*
* this table contains the types of employments
eG: Work from Office Full-Time / Part-Time, Work from Home Full-Time / Part-Time Etc.
* Use The Script from Folder Inserts/Employments_Insert.txt
*/
@Inserts/Employments_Insert.txt
--select * from Employments;

-- 12. -------------- Insert Departments --------------
/*
* this table contains the departments names
* use the script from folder Inserts/Departments_insert.txt
*/

@Inserts/Departments_Insert.txt
--select * from Departments;

-- 13. -------------- Insert Jobs --------------
/*
* this table contains different types of jobs
* use the script from folder Inserts/Jobs_inserts.txt
*/

@Inserts/Jobs_inserts.txt
--select * from Jobs;

-- 14. -------------- Insert Time_Types --------------
/*
* this table contains different time types ( regular, overtime etc )
* use the script from folder Inserts/Time_Types_inserts.txt
*/
@Inserts/Time_Types_inserts.txt
--select * from Time_Types;

-- 15. -------------- Insert Projects --------------
/*
* this table contains different projects
* use the script from folder Inserts/Projects_inserts.txt
*/
@Inserts/Projects_inserts.txt
--select * from Projects;


-- 16. -------------- Insert Employees --------------
/*
* this table contains the employees
* use the script from folder Inserts/Employees_inserts.txt
*/
@Inserts/Employees_inserts.txt
--select * from Employees;


-- 16. -------------- Insert Employees_Projects --------------
/*
* this table contains the employees_Projects
* use the script from folder Inserts/Employees_Projects_inserts.txt
*/
@Inserts/Employees_Projects_inserts.txt
--select * from Employees_Projects;



-- 17. -------------- Insert Timesheets --------------
/*
* this table contains the timesheets records
* use the script from folder Inserts/Timesheets_inserts.txt
*/
@Inserts/Timesheets_inserts.txt
--select * from Timesheets;



-- 18. -------------- Triggers -------------------

-- Test the trigger for insert in timesheet in the future. Today is 11 june so the query is for 12 june
-- insert INTO Timesheets (timesheet_id, employee_project_id, time_type_id, day_of_work, hours_per_day) VALUES (990, 'EP103005', 'OVT', DATE '2025-06-12', 7);



/* This trigger will be actioned in the next cases:
Case 1. An user with a specific type of employment can only have the same amount of hours added as <regular> in timesheet per day. 
    eg: If user with employee_id=100 have a full-time 8 hours employment, his record in timesheet as a <regular> record must be <= 8. 
Trigger is actioned if hours_per_day > 8. Same for the employment of 7,6,4 hours / day

Case 2. Ensure an employee’s total regular hours per day do not exceed their allowed daily hours, even when split across multiple projects.
 (E.g. One employee ( with full-time 8 hours ) could log 4 h on PRJ001 and 4 h on PRJ005 -> total 8 regular hours ... but not 5 h + 4 h.)
 
Case 3. Any overtime record can't be more than 6 hours per day.
*/

CREATE OR REPLACE TRIGGER trg_timesheet_hour_limits
BEFORE INSERT OR UPDATE ON Timesheets
FOR EACH ROW
DECLARE
  v_emp_id        Employees.employee_id%TYPE;
  v_daily_hours   Programs.daily_hours%TYPE;
  v_existing_reg  NUMBER;
BEGIN
  IF :NEW.time_type_id = 'REG' THEN
    -- find the employee for this employee_project_id
    SELECT ep.employee_id
      INTO v_emp_id
      FROM Employees_Projects ep
     WHERE ep.employee_project_id = :NEW.employee_project_id;

    -- look up that employee's daily_hours via Employments→Programs
    SELECT p.daily_hours
      INTO v_daily_hours
      FROM Programs p
      JOIN Employments e ON e.program_id = p.program_id
      JOIN Employees emp ON emp.employment_id = e.employment_id
     WHERE emp.employee_id = v_emp_id;

    -- Requirement 1: per-row check that a single REG entry’s hours ≤ daily_hours
    IF :NEW.hours_per_day > v_daily_hours THEN
      RAISE_APPLICATION_ERROR(
        -20001,
        'Inserted regular hours (' || :NEW.hours_per_day ||
        ') exceed daily limit of ' || v_daily_hours || ' hours of employment contract.'
      );
    END IF;
    
    /*
    IF :NEW.hours_per_day = v_daily_hours THEN
      RAISE_APPLICATION_ERROR(
        -20001,
        'This user is recorded with ' || :NEW.hours_per_day ||
        ' regular hours on ' || :NEW.day_of_work
      );
    END IF;*/

    -- compute sum of existing REGular hours for that employee on this new date
    SELECT NVL(SUM(ts.hours_per_day),0)
      INTO v_existing_reg
      FROM Timesheets ts
      JOIN Employees_Projects ep2
        ON ts.employee_project_id = ep2.employee_project_id
     WHERE ep2.employee_id   = v_emp_id
       AND ts.time_type_id   = 'REG'
       AND ts.day_of_work    = :NEW.day_of_work;

    -- Requirement 2: cumulative check that (existing + new) REG hours ≤ inserted daily_hours
    IF v_existing_reg - :NEW.hours_per_day > 0
       AND v_existing_reg + :NEW.hours_per_day > v_daily_hours
    THEN
      RAISE_APPLICATION_ERROR(
        -20002,
        'This user is already recorded with ' || v_existing_reg ||
        ' regular hours on ' || TO_CHAR(:NEW.day_of_work,'YYYY-MM-DD') ||
        ', so you cannot add your new ' || :NEW.hours_per_day || ' hours.'
      );
    END IF;

  ELSIF :NEW.time_type_id = 'OVT' THEN
    -- Requirement 3: OVT entries cannot exceed 6 hours per day
    IF :NEW.hours_per_day > 6 THEN
      RAISE_APPLICATION_ERROR(
        -20003,
        'No more than 6 hours overtime per day'
      );
    END IF;
  END IF;
END;
/




-- 19. --------------- TESTING THE TRIGGER --------------
/* Use case 1
-- this insert have more hours than user employment allow as regular hours

insert  INTO Timesheets (timesheet_id, employee_project_id, time_type_id, day_of_work, hours_per_day) VALUES (992, 'EP100001', 'REG', DATE '2025-06-11', 9);

*/


/* Use case 1+2

-- this insert will be recorded with success

insert INTO Timesheets (timesheet_id, employee_project_id, time_type_id, day_of_work, hours_per_day) VALUES (993, 'EP103004', 'REG', DATE '2025-06-10', 4);
commit;

-- this record will trigger because hours_per_day form insert + the 4 hours of previous insert ( both at 10 june 2025 ) are grater than employee's employment hours

insert INTO Timesheets (timesheet_id, employee_project_id, time_type_id, day_of_work, hours_per_day) VALUES (994, 'EP103005', 'REG', DATE '2025-06-10', 7);
*/

/* Use case 3

insert INTO Timesheets (timesheet_id, employee_project_id, time_type_id, day_of_work, hours_per_day) VALUES (995, 'EP103005', 'OVT', DATE '2025-06-11', 7);
*/
 



-- 20. --------------- VIEW --------------

-- View showing only employees who have logged timesheet entries,
-- including the date, type of time, hours worked, and project name.
CREATE OR REPLACE VIEW vw_all_employees_times AS
SELECT
  e.employee_id,
  e.first_name || ' ' || e.last_name AS "Employee",
  ts.day_of_work     AS "Day of record",
  tt.name           AS "Type of record",
  ts.hours_per_day  AS "Hours per day",
  p.name            AS "Project name"
FROM Timesheets      ts
  JOIN Employees_Projects ep
    ON ts.employee_project_id = ep.employee_project_id
  JOIN Employees     e
    ON ep.employee_id = e.employee_id
  JOIN Time_Types     tt
    ON ts.time_type_id = tt.time_type_id
  JOIN Projects      p
    ON ep.project_id = p.project_id;

select * from vw_all_employees_times;




-- 21. --------------- Materialized View --------------

/*
This materialized view stores the total timesheet hours each employee has logged on a selected project.
*/

-- Drop the materialized view if neccesarly
-- DROP MATERIALIZED VIEW mv_project_hours;

-- 2) Recreate it properly
CREATE MATERIALIZED VIEW mv_project_hours
  BUILD IMMEDIATE
  REFRESH COMPLETE
  ON DEMAND
AS
SELECT
  ep.employee_id                           AS employee_id,
  e.first_name || ' ' || e.last_name       AS full_name,
  ep.project_id                            AS project_id,
  p.name                                    AS project_name,
  SUM(t.hours_per_day)                      AS total_hours
FROM Timesheets t
JOIN Employees_Projects ep
  ON t.employee_project_id = ep.employee_project_id
JOIN Employees e
  ON ep.employee_id = e.employee_id
JOIN Projects p
  ON ep.project_id = p.project_id
GROUP BY
  ep.employee_id,
  e.first_name,
  e.last_name,
  ep.project_id,
  p.name;


-- exemple 1: 
SELECT *
  FROM mv_project_hours
 WHERE Project_ID = 'PRJ001';
 
 -- example 2
SELECT *
  FROM mv_project_hours
 WHERE Project_ID = 'PRJ004';




-- 22. --------------- Select using GROUP BY --------------

-- Total regular hours per employee
SELECT 
  e.employee_id,
  e.first_name || ' ' || e.last_name AS full_name,
  SUM(ts.hours_per_day) AS total_reg_hours
FROM Employees e
JOIN Employees_Projects ep 
  ON e.employee_id = ep.employee_id
JOIN Timesheets ts 
  ON ep.employee_project_id = ts.employee_project_id
WHERE ts.time_type_id = 'REG'
GROUP BY 
  e.employee_id, 
  e.first_name, 
  e.last_name;



-- 23. --------------- Select using Left join --------------

-- Show every employee and any hours they logged on 2025-06-10 (0 if none)
SELECT
  e.employee_id,
  e.first_name || ' ' || e.last_name AS full_name,
  NVL(
    SUM(ts.hours_per_day),
    0
  ) AS hours_on_2025_06_10
FROM Employees e
LEFT JOIN Employees_Projects ep 
  ON e.employee_id = ep.employee_id
LEFT JOIN Timesheets ts 
  ON ep.employee_project_id = ts.employee_project_id
     AND ts.day_of_work = DATE '2025-06-05'
GROUP BY
  e.employee_id,
  e.first_name,
  e.last_name
ORDER BY
  e.employee_id;


-- 24. --------------- Select using analytical function --------------

-- Ranking employees by their total REGular hours using RANK():
SELECT
  RANK() 
    OVER (ORDER BY total_regular_hours DESC) AS regular_hours_rank,
  employee_id,
  total_regular_hours
FROM (
  SELECT 
    ep.employee_id,
    SUM(ts.hours_per_day) AS total_regular_hours
  FROM Timesheets ts
  JOIN Employees_Projects ep 
    ON ts.employee_project_id = ep.employee_project_id
  WHERE ts.time_type_id = 'REG'
  GROUP BY ep.employee_id
);


