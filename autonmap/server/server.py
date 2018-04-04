#!/usr/bin/env python3

import os
import signal
import socketserver
import threading
from os.path import join
from sqlite3 import ProgrammingError
from subprocess import Popen
from threading import Thread
from time import sleep
import base64
import zlib

from libnmap.parser import NmapParserException

from autonmap.server import data_parser
from autonmap.server import database_server
from autonmap.server import server_config

work_to_do = list()
received_data = dict()

work_command = server_config.get_client_commands("request_job")


class SignalWatch:
    kill = False

    def __init__(self):
        signal.signal(signal.SIGINT, self._exit)
        signal.signal(signal.SIGTERM, self._exit)

    def _exit(self, signum, frame):
        self.kill = True


is_alive = False

database = database_server.DatabaseManager()
signal_watch = SignalWatch()


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self, retries=0):
        try:
            data = str(self.request.recv(1024), 'utf-8')
        except ConnectionResetError as error:
            print("Connection reset by: {}".format(error))
        global work_to_do
        if len(work_to_do) == 0:
            update_work()
        if data == work_command:
            if work_to_do:
                response = zlib.compress(base64.b64encode("job: {}".format(work_to_do.pop()).encode("utf-8")), 9)
            else:
                response = zlib.compress(base64.b64encode("NO WORK".encode("utf-8")), 9)
            self.request.sendall(response)
            print("handed out work to {} with work of {}.".format(self.client_address, response))
        elif "n data\n" in data:
            r_data = []
            while True:
                try:
                    r_data.append(data.replace("n data\n", "").replace("end\r\n", ""))
                except MemoryError:
                    sleep(0.5)
                    try:
                        r_data.append(data.replace("n data\n", "").replace("end\r\n", ""))
                    except MemoryError or OSError:
                        return False
                if "end\r\n" in data:
                    break
                else:
                    data = str(self.request.recv(1024), 'utf-8')
            process_data(r_data, self.client_address)
            print("Connection closed with {}".format(self.client_address))
        else:
            self.request.sendall(bytes("{}: {}".format(threading.current_thread(), data), 'ascii'))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def update_work():
    global work_to_do
    try:
        with open(join(server_config.get_base(), "work.txt"), "r") as file:
            for line in file:
                l = line.strip("\n")
                if l:
                    work_to_do.append(l)
    except FileNotFoundError:
        with open(join(server_config.get_base(), "work.txt"), "w") as file:
            file.write("127.0.0.1")
        update_work()
    complete = set()
    with database_server.DatabaseManager() as db:
        db.open()
        for ip in db.get_info("IPADDR"):
            for ipa in ip:
                complete.add(ipa)
    use = set(".".join(word.split('.')[:-1]) for word in complete)
    work_to_do = [ip for ip in work_to_do if ".".join(ip.split('.')[:-1]) not in use]


def save_work():
    global work_to_do
    with open(join(os.path.dirname(os.path.realpath(__file__)), "work.txt"), "r") as file:
        for line in work_to_do:
            file.write(line.strip("\n"))


def process_data(data, peer, tries=0):
    def _process_data(_data):
        print("Adding data to database")
        with database_server.DatabaseManager() as _db:
            n_data = data_parser.parse("".join(data))
            for host in n_data.hosts:
                _db.add_ip_scan(ipaddr=host.address, port_data=host.get_open_ports(), e_time=n_data.elapsed,
                               source_ip=peer, command=n_data.commandline, raw_data=_data)
            print("Finished adding data to database")

    try:
        t = Thread(target=_process_data, args=(data,))
        t.start()
        t.join()
        return t
    except NmapParserException:
        with database_server.DatabaseManager() as db:
            db.bad_data(_data=data)
    except ProgrammingError:
        if tries < 2:
            process_data(data=data, peer=peer, tries=tries+1)
        else:
            try:
                database.close()
            except ProgrammingError:
                print("Database failed to close correctly, continuing")
            database.open()
            database.bad_data(_data=data)


def main():
    global work_to_do
    global is_alive
    global database
    global signal_watch

    db_path = database.path

    database.open()
    database.close()

    Popen(['sudo', 'chmod', 'a=rwx', db_path])

    host = server_config.get_global("server_ip")
    port = int(server_config.get_global("server_port"))
    server = ThreadedTCPServer((host, port), ThreadedTCPRequestHandler)

    work_to_do = []
    update_work()

    server.daemon_threads = True
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    is_alive = True
    print("Server is now up and ready to server work!")

    while not signal_watch.kill:
        sleep(1)
        pass

    server.shutdown()
    server.server_close()
    database.close()

    Popen(['sudo', 'chmod', 'a=rx,u=rwx', db_path])

    is_alive = False


if __name__ == "__main__":
    main()
