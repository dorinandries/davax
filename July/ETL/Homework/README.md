
# 📘 ETL homework project

## 📌 Overview

This project implements a full **ETL (Extract-Transform-Load)** pipeline designed to process employee and training data, normalize it, and store it for analytical purposes in a structured data warehouse environment. It also includes the generation of PDF reports based on specific business questions.

---

## 🏗️ Project structure

The project consists of several components organized under dedicated folders:

```
ETL_Homework_Project/
├── ___Extract/
├── __Transform/
├── _Load/
├── duAbsences/
├── etl/
├── rapoarte/
├── sqlWorksheetFiles/
└── README.md
```

---

## 🧩 Database users and tables

### 1. **etl_src_user**
- **Purpose**: Initial raw data storage.
- **Tables**:
  - Denormalized structure, with `NULL` values.
  - Populated via Python scripts from `.csv` files (located in `Extract/` folder).

### 2. **etl_stg_user**
- **Purpose**: Staging layer with normalized data.
- **Tables**:
  - `DIM_STG_ABSENCES` & `DIM_STG_ABSENCE_CODES` ← `DIM_RAW_ABSENCES`
  - `DIM_STG_EMPLOYEES_ON_TRAINING` & `DIM_STG_TRAINING_SESSION` ← `DIM_RAW_TRAINING_ATTENDANCE`
  - `DIM_STG_EMPLOYEE` ← Filtered from `DIM_RAW_ABSENCES` (only employees from Suceava and Brașov DUs)

### 3. **etl_tgt_user**
- **Purpose**: Target schema with facts and dimensions.
- **Tables**:
  - **Fact Tables**:
    - `FACT_TGT_EMPLOYEE`
    - `FACT_TGT_EMPLOYEES_ON_TRAINING`
    - `FACT_TGT_TIMESHEET`
  - **Dimension Tables**:
    - `DIM_TGT_EMPLOYEE_HISTORY` (used with `FACT_TGT_EMPLOYEE` in an **SCD2** setup)
    - `DIM_TGT_ABSENCES`
    - `DIM_TGT_PROJECT`
    - `DIM_TGT_TRAINING_SESSION`
    - `DIM_TGT_DATE` (records all days between **May 1st and August 31st**, 2025)

---

## 🛠️ ETL process

- **Extract**: Loads `.csv` files into `etl_src_user` tables.
- **Transform**: Normalizes the data and removes nulls, populating staging tables.
- **Load**: Inserts final cleaned and structured data into target fact/dimension tables.

---


## 🔧 Configuration

### Initial Setup Steps

To prepare your Oracle environment using Docker and SQL Developer:
1. Use Rancher Desktop as a container visualization tool.

2. Create a Docker volume
```bash
docker volume create oracle_data_vol
```

3. Create a dedicated Oracle container with attached volume
```bash
docker run -d --name oracle_timesheet -p 1522:1521 -e ORACLE_PWD=your_main_password -v oracle_data_vol:/opt/oracle/oradata container-registry.oracle.com/database/enterprise:latest
```

4. Connect in SQL Developer:
```text
- Username: sys
- Role: SYSDBA
- Service Name: ORCLPDB1
```


### Python Script Execution Requirements:
```bash
pip install reportlab
pip install matplotlib
pip install "setuptools<81"
```

### .ENV Configuration

```env
# Global Oracle DB Connection Parameters
ORACLE_USER=your_main_user
ORACLE_PASSWORD=your_main_password

# Source Schema Credentials
ORACLE_USER_SRC=etl_src_user
ORACLE_PASSWORD_SRC=your_src_password

# Staging Schema Credentials
ORACLE_USER_STG=etl_stg_user
ORACLE_PASSWORD_STG=your_stg_password

# Target Schema Credentials
ORACLE_USER_TGT=etl_tgt_user
ORACLE_PASSWORD_TGT=your_tgt_password

# Oracle DSN Format: host:port/service_name
# Replace "host.docker.internal" with:
#  - `localhost` if running locally
#  - Container IP if running in a container network
#  - Use port `1522` as mapped in the Docker command

ORACLE_DSN=host.docker.internal:1522/ORCLPDB1

```

---

## 📂 Folder details

- `___Extract/`: Loads raw `.csv` data into source tables.
- `__Transform/`: Normalizes and processes raw data for staging.
- `_Load/`: Loads data into dimension and fact tables.
- `etl/` & `duAbsences/`: Contain preprocessed `.csv` files.
- `rapoarte/`: Contains:
  - Python scripts for generating reports
  - Output `.pdf` reports
- `sqlWorksheetFiles/`: Contains all SQL scripts used to configure and populate the Oracle database:

  | File | Description |
  |------|-------------|
  | `timesheet_tema1_config.sql` | Initial environment setup: creates tablespaces, and defines users (`etl_src_user`, `etl_stg_user`, `etl_tgt_user`) with required grants and quotas. |
  | `timesheet_etl_sources.sql` | Creates **source-level raw tables** (`DIM_RAW_DU_ABSENCES`, `DIM_RAW_TRAINNING_ATTENDANCE`) for extracting initial unprocessed data. |
  | `timesheet_etl_stages.sql` | Defines **staging-level normalized tables** such as `DIM_STG_EMPLOYEE`, `DIM_STG_ABSENCES`, `DIM_STG_TRAINING_SESSION`, and `DIM_STG_EMPLOYEES_ON_TRAINING`. |
  | `timesheet_etl_target.sql` | Sets up **target fact and dimension tables**, including `FACT_TGT_TIMESHEET`, `DIM_TGT_DATE`, and implements **SCD2 logic** using triggers and sequences on employee data. |

---

## 📊 Reports and business questions

### Q1: **Who missed the ETL training sessions and why?**
- Check:
  - `Who missed the Dava.X Academy - ETL Theory training sessions 1 and why.pdf`
  - `... sessions 2 and why.pdf`
  - `... sessions 3 and why.pdf`

### Q2: **Details about each training session?**
- See:
  - `Details about Dava.X Academy - ETL Theory training sessions 1.pdf`
  - `... sessions 2.pdf`
  - `... sessions 3.pdf`

### Q3: **How many people took time off from DAVA academy and why?**
- Refer to: `Raport_Grafic_Numar_Absente.pdf`

### Q4: **What did employee X do between June 1 – August 31, 2025?**
- Analyzed using joins between:
  - `FACT_TGT_TIMESHEET`
  - `DIM_TGT_ABSENCES`
  - `DIM_TGT_DATE`
  - `DIM_TGT_TRAINING_SESSION`
- See: `Employee_Activity_June_2025.pdf`

---

## 🔁 SCD2

- Managed via **SQL Developer** using a **trigger**.
- Automatically inserts records and updates `DIM_TGT_EMPLOYEE_HISTORY` to maintain historical integrity for employee changes.

---

## ✅ Notes

- `DIM_TGT_DATE` allows for rich time-based analytics (beyond a simple `dateID`).
- No calendar logic (e.g., weekend calculation) is embedded—data is loaded once efficiently.
- Extra attention was given to maintaining **data integrity**, **historical accuracy**, and **modularity** in code and DB design.
