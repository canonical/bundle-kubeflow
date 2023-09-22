
# Charmed Kubeflow Databases Migration Guide

 When upgrading to Charmed Kubeflow 1.8 the databases must be migrated to MySQL. There are two databases in Charmed Kubeflow - `katib-db` and `kfp-db`. In Charmed Kubeflow 1.7 these databases are backed by the `charmed-osm-mariadb-k8s` charm. In the same release (1.7) we introduced support for MySQL databases, which can be deployed using the `mysql-k8s` charm. In Charmed Kubeflow 1.8 release MariaDB is not supported. Databases must be migrated prior to upgrading to Charmed Kubeflow 1.8. Migration process describe is only applicable for migration from CKF 1.7 to 1.8.

## Do you need to migrate?

A database migration is only required if the output of the following command is `mariadb-k8s`:


```python
    # replace DB_CHARM with desired unit name: `katib-db` or `kfp-db`
    DB_CHARM= <kfp-db | katib-db>
    juju show-application $DB_CHARM | yq '.[] | .charm'
```

## Prerequisites

- Client machine with access to deployed Charmed Kubeflow 1.7.
- Juju version 2.9.
- Enough storage in the cluster to support backup/restore of the databases.
- `mysql-client` on client machine (install by running `sudo apt install mysql-client`).

## Obtain existing database credentials

To obtain credentials for existing databases execute the following commands for each database to be migrated. Use those credentials in migration steps.


```python
# replace DB_UNIT with desired unit name: `katib-db/0` or `kfp-db/0`
DB_UNIT= <katib-db/0 | kfp-db/0>

# obtain username and password of existing MariadDB database from DB relation
# in Charmed Kubeflow 1.7 username used is `root` and password is specified in `mysql` relation by
# 'root_password'
DB_MYSQL_RELATION_ID=$(juju show-unit $DB_UNIT | yq '.[] | .relation-info | select(.[].endpoint == "mysql") | .[0] | .relation-id')
DB_USER=root
DB_PASSWORD=$(bash -c "juju run --unit $DB_UNIT 'relation-get -r $DB_MYSQL_RELATION_ID - $DB_UNIT' | grep root_password" | awk '{print $2}')
DB_IP=$(juju show-unit $DB_UNIT | yq '.[] | .address')
```

## Deploy new MySQL databases and obtain credentials

Deploy new MySQL databases and obtain credentials for each new database by executing the following commands, once per database:


```python
# replace MYSQL_DB with desired application name: `katib-db-mysql` or `kfp-db-mysql`
MYSQL_DB= <katib-db-mysql | kfp-db-mysql>

# deploy new MySQL database charm
juju deploy mysql-k8s $MYSQL_DB --channel 8.0/stable --trust

# obtain username and password of new MySQL database from MySQL charm
MYSQL_DB_USER=$(juju run-action $MYSQL_DB/0 get-password --wait | yq '.[] | .results.username')
MYSQL_DB_PASSWORD=$(juju run-action $MYSQL_DB/0 get-password --wait | yq '.[] | .results.password')
MYSQL_DB_IP=$(juju show-unit $MYSQL_DB/0 | yq '.[] | .address')

```

## Katib DB migration

Use the credentials and information obtained in previous steps for `katib-db` to perform the database migration by executing the following commands:


```python
# ensure that there are no new connections are made and that dababase is not altered
# remove relation between katib-db-manager charm and katib-db charm
juju remove-relation katib-db-manager katib-db

# connect to unit's IP address using mysql client and verify that `katib` database exists
# this command will log you into mysql monitor prompt
mysql --host=$DB_IP --user=$DB_USER --password=$DB_PASSWORD

# exit mysql client session

# create backup of all databases file using `mysqldump` utility, username, password, and unit's IP address
# obtained earlier
# file `katib-db.sql` will be created that can be used to restore database
mysqldump --host=$DB_IP --user=$DB_USER --password=$DB_PASSWORD --column-statistics=0 --databases katib  > katib-db.sql

# connect to new DB using username, password, and unit's IP address and restore database from backup
mysql --host=$MYSQL_DB_IP --user=$MYSQL_DB_USER --password=$MYSQL_DB_PASSWORD < katib-db.sql

# relate katib-db-manager and new MySQL database charm
juju relate katib-db-manager:relational-db $MYSQL_DB:database
```

## KFP DB migration

Use the credentials and information obtained in the previous steps for `kfp-db` to perform the database migration by executing the following commands:


```python
# ensure that there are no new connections are made and that dababase is not altered
# remove relation between kfp-api charm and kfp-db charm
juju remove-relation kfp-api kfp-db

# connect to unit's IP address using mysql client and verify that `mlpipeline` database exists
# this command will log you into mysql monitor prompt
mysql --host=$DB_IP --user=$DB_USER --password=$DB_PASSWORD

# exit mysql client session

# create backup of all databases file using `mysqldump` utility, username, password, and unit's IP address
# obtained earlier
# file `kfp-db.sql` will be created that can be used to restore database
mysqldump --host=$DB_IP --user=$DB_USER --password=$DB_PASSWORD --column-statistics=0 --databases mlpipeline  > kfp-db.sql

# connect to new DB using username, password, and unit's IP address and restore database from backup
mysql --host=$MYSQL_DB_IP --user=$MYSQL_DB_USER --password=$MYSQL_DB_PASSWORD < kfp-db.sql

# relate kfp-api and new MySQL database charm
juju relate kfp-api:relational-db $MYSQL_DB:database
```

## Verify DB migration

Note: some variables will vary per Katib vs. KFP, namely: `$MYSQL_DB_PASSWORD` and `$MYSQL_DB_IP`. These must be adjusted for the correct database, accordingly.


```python
# compare new MySQL database and compare it to the backup created earlier
mysqldump --host=$MYSQL_DB_IP --user=$MYSQL_DB_USER --password=$MYSQL_DB_PASSWORD --column-statistics=0 --databases katib  > katib-db-new.sql
diff katib-db.sql katib-db-new.sql
mysqldump --host=$MYSQL_DB_IP --user=$MYSQL_DB_USER --password=$MYSQL_DB_PASSWORD --column-statistics=0 --databases mlpipeline  > kfp-db-new.sql
diff kfp-db.sql kfp-db-new.sql
```

The difference between two SQL backup files should be limited to server versions, IP addresses, timestamps and other non data related information. Example of difference:


```python
< -- Host: 10.1.45.226    Database: katib
---
> -- Host: 10.1.46.40    Database: katib
5c5
< -- Server version	5.5.5-10.3.17-MariaDB-1:10.3.17+maria~bionic
---
> -- Server version	8.0.34-0ubuntu0.22.04.1
16a17,26
> SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
> SET @@SESSION.SQL_LOG_BIN= 0;
> 
> --
> -- GTID state at the beginning of the backup 
> --
> 
> SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '0d3210b9-587f-11ee-acf3-b26305f815ec:1-4,
> 34442d83-587f-11ee-84f5-b26305f815ec:1-85,
> 34444583-587f-11ee-84f5-b26305f815ec:1';
22c32
< CREATE DATABASE /*!32312 IF NOT EXISTS*/ `katib` /*!40100 DEFAULT CHARACTER SET latin1 */;
---
> CREATE DATABASE /*!32312 IF NOT EXISTS*/ `katib` /*!40100 DEFAULT CHARACTER SET latin1 */ /*!80016 DEFAULT ENCRYPTION='N' */;
34c44
<   `id` int(11) NOT NULL,
---
>   `id` int NOT NULL,
60c70
<   `id` int(11) NOT NULL AUTO_INCREMENT,
---
>   `id` int NOT NULL AUTO_INCREMENT,
75a86
> SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
86c97
< -- Dump completed on 2023-09-21 17:05:54
---
> -- Dump completed on 2023-09-21 17:09:40

```

## Remove old databases


```python
juju remove-application --destroy-storage katib-db kfp-db 
```
