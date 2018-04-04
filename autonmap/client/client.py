#!/usr/bin/env python3
import signal
import subprocess
from time import sleep
from os.path import join
from dateutil.parser import parse
from datetime import datetime

from autonmap.client import client_server
from autonmap.client import config_manager
from autonmap.client import process_manager
from autonmap.client import report_client

"""
This module controls all client processes of the autonmap program
"""

__LOCKFILE_NAME__ = "processmanager.lock"


class Lock:
    def __init__(self):
        self.lock = False
        self.locate_lock()

    def locate_lock(self):
        from os import walk
        for root, dirs, files in walk(config_manager.get_base()):
            if __LOCKFILE_NAME__ in files:
                self.lock = True

    def release_lock(self):
        from os import remove
        try:
            remove(join(config_manager.get_base(), __LOCKFILE_NAME__))
            self.lock = False
        except OSError:
            return False

    def get_lock(self):
        with open(join(config_manager.get_base(), __LOCKFILE_NAME__), "w") as file:
            pass
        self.lock = True


class Timeout:
    class Timeout(Exception):
        pass

    def __init__(self, sec=0):
        self.sec = sec

    def raise_timeout(self, *args):
        raise self.Timeout()

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)


class Client:
    """
    Module that controls several subprocess that work together to
    complete work handed out.
    """

    def __init__(self):
        self.conn = client_server.ClientServer()
        self.process = process_manager.ProcessManager()
        self.server_ip = config_manager.get_global("server_ip")
        self.server_port = int(config_manager.get_global("server_port"))
        self.report_manager = report_client.ReportManger()
        self.lock = Lock()

    def do_work(self):
        """
        This function asks for work from the server and after it receives the work to
        be completed it will then initiate the process required to begin the work.
        :return: None
        """
        sleeps = 0
        while self.lock.lock:
            print("Process Locked cannot gather work. Sleeping for 1 min.")
            sleep(60)
            processes = subprocess.Popen(["pgrep", 'autonmap'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes = processes.communicate()
            processes = str(processes[0], 'ascii').split("\n")
            print(processes)
            if not processes or len(processes) == 2:
                print("Nothing blocking process, releasing lock")
                self.lock.release_lock()
                break
            while processes:
                proc = processes.pop()
                print("Found Process {}".format(proc))
                print("Process ID that is halting the program: ".format(proc))
                print("Checking if process has run for too long and is stuck.")
                p = subprocess.Popen(['ps', '-o', 'stime,time', proc], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                try:
                    p = parse(str(p.communicate()[0], 'ascii'))
                except ValueError:
                    continue
                if (datetime.now() - p).seconds > 7200:
                    print("Killing process: {}".format(proc))
                    com = subprocess.Popen(['kill', '-9', proc], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    com = com.communicate()
                    print("Process Kill Attempt OUT: {}\tERROR: {}".format(str(com[0], 'ascii'),
                                                                           str(com[1], 'ascii')))
                    if str(com[1], 'ascii'):
                        print("Found error {}, breaking from process search".format(com[1]))
                        break
                else:
                    break
            sleeps += 1
            if sleeps > 10:
                print("Failed to find get work!!!")
                return False
        else:
            print("No process blocking, releasing lock.")
            self.lock.release_lock()
        self.lock.get_lock()
        print("Acquired Lock.")
        self.conn.connect(self.server_ip, self.server_port)
        self.conn.send(config_manager.get_client_commands("request_job"))
        self.conn.receive()
        jobs = self.conn.do_job()
        self.conn.close()
        print("Adding work to the process manager")
        for host in jobs:
            print(host)
            self.process.add_host(host)
        print("Hosts added to process manager, starting work.")
        print("----------------------------------------------")
        self.process.run()
        self.lock.release_lock()
        print("Work Completed, Running the report manager.")
        print("----------------------------------------------")
        self.report_manager.generate_database_report()
        print("Report filed, releasing lock.")
        self.lock.release_lock()

    def stop(self):
        """
        This function sends the kill signal to the worker process and tries to shut them down.
        :return: None
        """
        print("Starting shutdown")
        self.process.exit.kill = True
        self.conn.close()
        self.lock.release_lock()
        print("Finished shutdown")


def main():
    """
    Function that initiates the sub-processes that find and complete the work.
    :return: None
    """
    client = Client()
    client.do_work()


if __name__ == "__main__":
    main()
