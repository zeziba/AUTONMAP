#!/usr/bin/env python3

import logging.handlers
import sys
from sys import argv, modules
from os.path import join

from autonmap import cron_scheduler
from autonmap import launch_client
from autonmap import launch_server
from autonmap.server import server_config as sconfig

"""
This module allows autonmap to interact with the server and client process to
preform the tasks each is assigned.
"""

LOG_FILE = "/tmp/autonmap.log"
LOGGING_LEVEL = logging.INFO

logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LEVEL)
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILE, when='midnight', backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Log(object):
    def __init__(self, log, level):
        self.logger = log
        self.level = level

    def write(self, message):
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())

    def flush(self):
        pass


def main():
    """
    Main routine
    :return: None
    """

    if len(argv) > 1:
        print("Automated nMap Server/Client Manager")
        if argv[1] == 'cron':
            cron_scheduler.main()
        elif argv[1] == "update":
            if len(argv) == 3:
                file_location = join(sconfig.get_base(), "work.txt")
                if str(argv[2]).lower() == "delete":
                    with open(file_location, "w") as file:
                        pass    # This empties the file of all contents
                else:
                    with open(argv[2], "r") as infile:
                        with open(file_location, "w+") as outfile:
                            subnets = set()
                            for in_line in infile:
                                subnets.add(in_line)
                            for out_line in outfile:
                                subnets.add(out_line)
                            outfile.seek(0)
                            outfile.truncate()
                            for item in subnets:
                                outfile.write("{}\n".format(item))
        elif len(argv) == 3:
            if argv[2] in ['start', 'stop', 'update', 'report']:
                if argv[1] == 'server':
                    sys.stdout = Log(log=logger, level=logging.INFO)
                    sys.stderr = Log(log=logger, level=logging.ERROR)
                    launch_server.main(argv[2])
                elif argv[1] == 'client':
                    sys.stdout = Log(log=logger, level=logging.INFO)
                    sys.stderr = Log(log=logger, level=logging.ERROR)
                    launch_client.main(argv[2])
            else:
                print("Invalid arguments")
        else:
            print("Invalid arguments")
    else:
        print("Usage: {} {} {}".format("python3 -m autonmap",
                                       "client|server|update", "start<client>|stop|report|update|"
                                                               "location<update>|delete<update>"))
        print("Usage: {} {}".format("python3 -m autonmap", "cron"))
        print("\t{} {}".format("python3 -m autonmap", "update ~/workfile.txt"))
        print("Client script is located at: \n\t\t{}".format(modules[launch_client.__name__]))
        print("The log is located in /tmp/autonmap.log")


if __name__ == "__main__":
    main()
