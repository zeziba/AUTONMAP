#!/usr/bin/env python3

import sys
from sys import argv

from autonmap.daemonizer import Daemon
from autonmap.server import server
from autonmap.server import server_config

"""
This module interfaces with the server process to provide a layer of abstraction to the server process.
"""

__base__ = server_config.get_base()


class Server(Daemon):
    """
    Daemonizes the server process
    """

    def run(self):
        self.server = server
        self.server.main()

    def quit(self):
        self.server.signal_watch.kill = True

    def update(self):
        self.server.update_work()


def main(arg):
    _daemon = Server()
    if arg == "start":
        print("Launching Server")
        _daemon.start()
    elif arg == 'stop':
        sys.stderr = sys.__stdout__
        print("Stopping server")
        _daemon.stop()
    elif arg == "update":
        print("Updating work list")
        _daemon.update()
    elif arg == 'report':
        print("Generating Report!")
        from autonmap.server import report_server
        report = report_server.ReportManger()
        report.generate_database_report()
        del report
    else:
        print("Usage: start|stop|update|report")


if __name__ == "__main__":
    if len(argv) > 1:
        main(argv[1])
    else:
        print("Usage: start|stop|update|report")
