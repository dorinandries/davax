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
  ) AS hours_on_2025_06_05
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


