#!/usr/bin/env python3

import base64
import sqlite3
import zlib
from os.path import join

from autonmap.client import client_server
from autonmap.client import config_manager

"""
This module is the interface for the client to the client sqlite database.
"""

_path_ = config_manager.get_base()

func_name = "raw_data"
table_name = "IPADDR_SCANS"

# This try statement checks the SQLite version, you might have to add more
# code here if you use version specific code. You will then have
# to tell the user that they failed to meet your requirements.
try:
    with sqlite3.connect(join(_path_, 'client.sqlite')) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT SQLITE_VERSION()')
        data = cursor.fetchone()
        # print("SQLite Version: %s" % data)
        cursor.execute('CREATE TABLE IF NOT EXISTS "%s" ("IPADDR" TEXT NOT NULL , '
                       '"TIMESTAMP" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, "port_data" TEXT,'
                       ' "exec-time" TEXT, "command" TEXT, "raw_data" TEXT)' % table_name)
except Exception as error:
    print("Failed to load Database")


class DatabaseManager:
    """
    Interface for the client database
    """

    def __init__(self):
        self.database = None
        self.command_list = []
        self.is_alive = False

    def _give_db_command(self, command, args=None):
        c = self.database.cursor()
        c.execute(command, args)

    def _insert_many(self):
        c = self.database.cursor()
        c.executemany("INSERT INTO IPADDR_SCANS('IPADDR', 'port_data', 'exec-time', 'command', 'raw_data')"
                           " VALUES(?, ?, ?, ?, ?)", self.command_list)
        self.command_list = []

    def commit(self):
        """
        Commit all commands queued in the database managers queue
        :return: None
        """
        self._insert_many()
        self.database.commit()

    def _rollback(self):
        self.database.rollback()

    def open_db(self, database=_path_):
        """
        Method opens the database connection
        :param database: override to database path
        :return: None
        """
        if not self.is_alive:
            self.database = sqlite3.connect(database=join(database, 'client.sqlite'))
            self.is_alive = True
        else:
            print("Database is already active.")

    def close_db(self):
        """
        Method closes the database connection
        :return: None
        """
        if self.is_alive:
            try:
                self.commit()
            except sqlite3.OperationalError:
                pass
            self.database.close()
            self.is_alive = False
        else:
            print("Database is not active.")

    def add_ip_scan(self, ipaddr, port_data, e_time, command, raw_data, _raw):
        """
        Method to handle adding ips data to the databasse
        :param ipaddr: ip address
        :param port_data: port information
        :param e_time: time to complete scan
        :param command: command used to execute
        :param raw_data: raw data dict
        :param _raw: raw data XML
        :return: None
        """
        self.command_list.append((ipaddr, str(port_data), str(e_time),
                                  zlib.compress(base64.b64encode(str(command).encode("utf-8")), 9),
                                  zlib.compress(base64.b64encode(str(raw_data).encode("utf-8")), 9)))
        self.__report_database(_raw)

    def del_ip_scan(self, ipaddr=None):
        #  TODO: abitity to delete scan data
        """
        Method to delete scan data
        :param ipaddr: ip address to delete
        :return: None
        """
        if ipaddr is not None:
            self._give_db_command("DELETE FROM IPADDR_SCANS WHERE IPADDR = (?)", ipaddr)
            return "{} entry was deleted".format(ipaddr)

    def get_info(self):
        """
        Method to get data from the database
        :return: yield all scan data
        """
        c = self.database.cursor()
        c.execute("SELECT * FROM 'IPADDR_SCANS'")
        _dat = sorted(c.fetchall())
        while _dat:
            yield _dat.pop()

    @staticmethod
    def __report_database(report_data):
        """
        Method sends a report to the server based on the data saved to the database
        :param report_data: raw data
        :return: None
        """
        print("Report function working")
        server = client_server.ClientServer()
        server_ip = config_manager.get_global("server_ip")
        server_port = int(config_manager.get_global("server_port"))
        server.connect(server_ip, server_port)
        server.send("n data\n")
        server.send(report_data)
        server.send("end\r\n")
        print("Report filed with server")


if __name__ == "__main__":
    db = DatabaseManager()
    db.open_db()
    status = db.is_alive
    for i in db.get_info():
        print(i)
    db.close_db()
    print("The database was {} created".format("successfully" if status else "was not"))
