#!/usr/bin/env python3

import base64
import zlib

from os import listdir
from os.path import join

from libnmap.parser import NmapParser, NmapReport

from autonmap.server import database_server
from autonmap.server import server_config as config_manager

# Report All hosts
__null__ = False

buffersize = 1


class ReportManger(NmapReport):
    def __init__(self):
        NmapReport.__init__(self)
        self.updated = False
        self.data_folder = config_manager.get_folder_path("data")
        self.database_conn = database_server.DatabaseManager()

    @staticmethod
    def files(folder):
        _data_folder = folder
        for file in listdir(_data_folder):
            yield join(_data_folder, file)

    def add_report(self, data):
        self.hosts.append(data)
        self.updated = True

    def _get_data(self):
        for host in self.files(self.data_folder):
            _h = NmapParser.parse_fromfile(host)
            for _host in _h.hosts:
                yield _host

    def to_file(self):
        with open("master_report.txt", "a+") as file:
            for host in self._get_data():
                file.write("{} \t{}\n".format(host.address, host.get_open_ports()))

    def _connect_to_database(self):
        self.database_conn.open()

    def _end_database_connection(self):
        self.database_conn.close()

    def generate_database_report(self):
        self._connect_to_database()

        report_header = "---START OF REPORT---\n{:<20}\t{:<23}\t{:<23}\t{:<8}\t{:<8}\t{:<16}\t{}\n". \
            format("IP_ADDR", "Source IP", "TIMESTAMP", "PROTOCOL", "PORT", "EXEC_TIME", "COMMAND_LINE_ARG")
        report = "{:<20}\t{:<23}\t{:<23}\t{:<8}\t{:<8}\t{:<16}\t{}\n"
        report_footer = "---END OF REPORT---"

        with open(join(config_manager.get_base(), 'data', "server_report.txt"), "w+", buffersize) as file:
            file.write(report_header)
            if not __null__:
                file.write("------OPTION: ALL PORTS SHOWN ARE OPEN------\n")
            data = [i for i in self.database_conn.get_info()]
            for index, d in enumerate(data):
                n_data = list(data[index])
                n_data[2] = eval(n_data[2])
                for _index, port in enumerate(n_data[2]):
                    file.write(report.format(n_data[0] if _index == 0 else "",  # Ip address
                                             n_data[4],                         # Source IP
                                             n_data[1],                         # TIMESTAMP
                                             port[1] if _index == 0 else "",    # Protocol
                                             port[0],                           # Port
                                             n_data[3] if _index == 0 else "",  # Execution time
                                                                                #  Command Line Arg
                                             base64.b64decode(zlib.decompress(n_data[5])) if _index == 0 else ""))
                else:
                    if __null__:
                        file.write(report.format(n_data[0], n_data[1], "NULL", "NULL", n_data[3], n_data[4]))
                del n_data
            file.write(report_footer)

        self._end_database_connection()


if __name__ == "__main__":
    rm = ReportManger()
    rm.generate_database_report()
