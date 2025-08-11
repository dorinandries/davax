/*
Pasii initiali:
1. Creare volum
    docker volume create oracle_data_vol
2. Creare container dedicat + volum pentru container pentru tema
    docker run -d --name oracle_timesheet -p 1522:1521 -e ORACLE_PWD=your_main_password -v oracle_data_vol:/opt/oracle/oradata container-registry.oracle.com/database/enterprise:latest
3. Conectare in SQLDeveloper cu sys as SYSDBA si ServiceName ORCLPDB1   
*/

-- Creare tablespace
CREATE TABLESPACE davax_data DATAFILE 'davax_data.dbf' SIZE 100M AUTOEXTEND ON NEXT 10M;
CREATE TABLESPACE davax_index DATAFILE 'davax_index.dbf' SIZE 50M AUTOEXTEND ON NEXT 5M;


GRANT SELECT ON V_$LOCKED_OBJECT TO etl_src_user;

-- Create sources user as Stage for ETL
CREATE USER etl_src_user IDENTIFIED BY etl_src_user_strong_password
  DEFAULT TABLESPACE davax_data 
  TEMPORARY TABLESPACE temp;

GRANT CONNECT, RESOURCE TO etl_src_user;
GRANT SELECT_CATALOG_ROLE TO etl_src_user;

GRANT CREATE TABLE, CREATE VIEW, CREATE SEQUENCE, CREATE TRIGGER TO etl_src_user;


ALTER USER etl_src_user QUOTA UNLIMITED ON davax_data;
ALTER USER etl_src_user QUOTA UNLIMITED ON davax_index;


-- Create sources user as Stage for ETL
CREATE USER etl_stg_user IDENTIFIED BY etl_stg_user_strong_password
  DEFAULT TABLESPACE davax_data 
  TEMPORARY TABLESPACE temp;

GRANT CONNECT, RESOURCE TO etl_stg_user;

GRANT SELECT_CATALOG_ROLE TO etl_stg_user;

GRANT CREATE TABLE, CREATE VIEW, CREATE SEQUENCE, CREATE TRIGGER TO etl_stg_user;


ALTER USER etl_stg_user QUOTA UNLIMITED ON davax_data;
ALTER USER etl_stg_user QUOTA UNLIMITED ON davax_index;


-- Create sources user as Stage for ETL
CREATE USER etl_tgt_user IDENTIFIED BY etl_tgt_user_strong_password
  DEFAULT TABLESPACE davax_data 
  TEMPORARY TABLESPACE temp;

GRANT CONNECT, RESOURCE TO etl_tgt_user;

GRANT SELECT_CATALOG_ROLE TO etl_tgt_user;

GRANT CREATE TABLE, CREATE VIEW, CREATE SEQUENCE, CREATE TRIGGER TO etl_tgt_user;


ALTER USER etl_tgt_user QUOTA UNLIMITED ON davax_data;
ALTER USER etl_tgt_user QUOTA UNLIMITED ON davax_index;
