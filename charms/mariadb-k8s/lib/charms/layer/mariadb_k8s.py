"""
Helpers for the mariadb-k8s charm.
"""

import mysql.connector


def create_database(cursor, db_name):
    cursor.execute('CREATE DATABASE IF NOT EXISTS %s', db_name)


def grant_exists(cursor, db_name, username, address):
    try:
        cursor.execute("SHOW GRANTS for %s@%s", username, address)
        grants = [i[0] for i in cursor.fetchall()]
    except mysql.connector.Error:
        return False
    else:
        return "GRANT ALL PRIVILEGES ON `{}`".format(db_name) in grants


def create_grant(cursor, db_name, username, password, address):
    cursor.execute("GRANT ALL PRIVILEGES ON %s.* TO %s@%s IDENTIFIED BY %s",
                   db_name, username, address, password)


def cleanup_grant(cursor, username, address):
    cursor.execute("DROP FROM mysql.user WHERE user=%s AND HOST=%s",
                   username, address)
