#!/usr/bin/env python3

import base64
import sqlite3
import zlib
from os.path import join
from sys import argv
from time import sleep

from autonmap.server import server_config

_path_ = server_config.get_base()

table_name = "IPADDR_SCANS"

# This try statement checks the SQLite version, you might have to add more
# code here if you use version specific code. You will then have
# to tell the user that they failed to meet your requirements.
try:
    with sqlite3.connect(join(_path_, 'server.sqlite')) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT SQLITE_VERSION()')
        data = cursor.fetchone()
        # print("SQLite Version: %s" % data)
        cursor.execute('CREATE TABLE IF NOT EXISTS "%s" ("IPADDR" TEXT NOT NULL , '
                       '"TIMESTAMP" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "port_data" TEXT,'
                       ' "exec-time", "source_ip" TEXT, "command" TEXT, "raw_data" TEXT)' % table_name)
        cursor.execute('CREATE  TABLE  IF NOT EXISTS "%s" '
                       '("data" TEXT NOT NULL , "TIMESTAMP" '
                       'DATETIME NOT NULL  DEFAULT CURRENT_TIMESTAMP)' % "BAD_DATA")

except Exception as error:
    print("Failed to load Database")
    print(error)
    print(Exception)


class DatabaseManager:
    def __init__(self, path=_path_):
        self.path = path
        self.database = None
        self.command_list = []
        self.is_alive = False

    def __enter__(self):
        self.open(database=self.path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.database.commit()
        self.close()

    def _give_db_command(self, command, args=None):
        c = self.database.cursor()
        c.execute(command, args)

    def _insert_many(self, timeout=2):
        c = self.database.cursor()
        for _ in range(timeout * 10):
            try:
                c.executemany("INSERT INTO IPADDR_SCANS"
                                   "('IPADDR', 'port_data', 'source_ip', 'exec-time', 'command', 'raw_data') "
                                   "VALUES(?, ?, ?, ?, ?, ?)", self.command_list)
            except:
                sleep(timeout / 10)
                pass
            finally:
                break
        else:
            c.executemany("INSERT INTO IPADDR_SCANS"
                               "('IPADDR', 'port_data', 'source_ip', 'exec-time', 'command', 'raw_data') "
                               "VALUES(?, ?, ?, ?, ?, ?)", self.command_list)
        self.command_list = []

    def commit(self):
        self._insert_many()
        self.database.commit()

    def _rollback(self):
        self.database.rollback()

    def open(self, database=_path_):
        if not self.is_alive:
            self.database = sqlite3.connect(database=join(database, 'server.sqlite'))
            self.is_alive = True
        else:
            print("Database is already active.")

    def close(self):
        if self.is_alive:
            self.commit()
            self.database.close()
            self.is_alive = False
        else:
            print("Database is not active.")

    def add_ip_scan(self, ipaddr, port_data, source_ip, e_time, command, raw_data):
        self.command_list.append((ipaddr, str(port_data), str(source_ip), str(e_time),
                                  zlib.compress(base64.b64encode(command.encode("utf-8")), 9),
                                  zlib.compress(base64.b64encode(str(raw_data).encode("utf-8")), 9)))

    def get_info(self, override=False):
        c = self.database.cursor()
        try:
            c.execute("SELECT {} FROM 'IPADDR_SCANS'".format(override if override else '*'))
        except sqlite3.OperationalError:
            print('{} does not exists in database'.format(override))
            return False
        _data = sorted(c.fetchall())
        while _data:
            yield _data.pop()

    def bad_data(self, _data):
        self.open()
        c = self.database.cursor()
        c.executemany("INSERT INTO BAD_DATA('data') VALUES(?)", _data)
        self.database.commit()


if __name__ == "__main__":
    if len(argv) > 1:
        if argv[1] == 'data':
            db = DatabaseManager()
            try:
                db.open(argv[2])
                for i in db.get_info():
                    print(i)
            except IndexError:
                db.open()
                for i in db.get_info():
                    print(i)
            db.close()
    else:
        db = DatabaseManager()
        db.open()
        status = db.is_alive
        for i in db.get_info():
            print(i)
        db.close()
        print("The database was {} created".format("successfully" if status else "was not"))
