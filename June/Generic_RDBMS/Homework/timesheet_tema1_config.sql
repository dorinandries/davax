/*
Pasii initiali:
1. Creare volum
    docker volume create oracle_data_vol
2. Creare container dedicat + volum pentru container pentru tema
    docker run -d --name oracle_timesheet -p 1522:1521 -e ORACLE_PWD=MySecurePassword -v oracle_data_vol:/opt/oracle/oradata container-registry.oracle.com/database/enterprise:latest
3. Conectare in SQLDeveloper cu sys as SYSDBA si ServiceName ORCLPDB1   
*/

-- Creare tablespace
CREATE TABLESPACE davax_data DATAFILE 'davax_data.dbf' SIZE 100M AUTOEXTEND ON NEXT 10M;
CREATE TABLESPACE davax_index DATAFILE 'davax_index.dbf' SIZE 50M AUTOEXTEND ON NEXT 5M;

-- Creare tema1_user din SYS
CREATE USER tema1_user IDENTIFIED BY tu 
  DEFAULT TABLESPACE davax_data 
  TEMPORARY TABLESPACE temp;

GRANT CONNECT, RESOURCE TO tema1_user;

ALTER USER tema1_user QUOTA UNLIMITED ON davax_data;
ALTER USER tema1_user QUOTA UNLIMITED ON davax_index;
GRANT CREATE ANY VIEW TO tema1_user;