#!/usr/bin/env python3
import base64
import socket
import zlib
from time import sleep

from autonmap.client import config_manager

"""
This module controls all access from the client to the server.
"""


class ClientServer:
    """
    Module controls a sockets to communicate with the server.
    """

    def __init__(self, family=socket.AF_INET, _type=socket.SOCK_STREAM, proto=0, fileno=None):
        self.family = family
        self.type = _type
        self.proto = proto
        self.fileno = fileno
        self.socket = socket.socket()
        self._connected = False
        self._connected_to = []
        self._received_data = []

    def _open(self):
        try:
            self.socket = socket.socket(family=self.family, type=self.type, proto=self.proto, fileno=self.fileno)
            return True
        except socket.error:
            print("Failed to create socket!")
            return False

    def connect(self, host, port, retry=0, wait_time=60, retries=2):
        """
        Opens a connection to a remote host.
        :param retries: retry attempt number
        :param wait_time: Time to wait in between tries
        :param retry: Max number of retries before it fails
        :param host: Ip address for host
        :param port: porty of host
        :return: True/False if succeeded in connecting
        """
        try:
            if not self._connected:
                self._open()
                try:
                    remote_ip = socket.gethostbyname(host)
                except socket.gaierror:
                    print("Could not resolve host")
                    return False
                self.socket.connect((remote_ip, port))
                print("Socket connected to {} on {}".format(remote_ip, port))
                self._connected_to = [remote_ip, port]
                self._connected = True
                return True
            else:
                print("Connection already exists!\nHOST: {}\tPORT: {}".format(*self._connected_to))
                return False
        except ConnectionRefusedError as error:
            print("Failed to make connection retrying in {} seconds".format(wait_time))
            if retry < retries:
                sleep(wait_time)
                self.connect(host=host, port=port, retry=retry+1)
            else:
                print("Failed to connect to socket, attempts exhausted.")
                raise error

    def close(self):
        """
        Method closes any open sockets to remote hosts.
        :return: True/False on success of closures
        """
        if self._connected:
            self.socket.close()
            self._connected = False
            print("Connection Closed at {} on {}".format(*self._connected_to))
            self._connected_to = []
            return True
        else:
            print("No connection exists!")
            return False

    def send(self, data):
        """
        Method that sends data over an open socket to a remote host
        :param data: Data to be passed to remote host, should be a string
        :return: True/False on success
        """
        if self._connected:
            try:
                if type(data) == bytes:
                    self.socket.sendall(data)
                else:
                    self.socket.sendall(data.encode())
            except socket.error:
                print("Failed to send data!")
            return True
        else:
            print("No Connection exists")
            return False

    def receive(self, buffer=4096, timeout=config_manager.get_timeout(), timeout_limit=3):
        """
        Method attempts to collect data from a remote host
        :param buffer: Size of the buffer
        :param timeout: time in seconds to wait for a timeout
        :param timeout_limit: Timeout limit
        :return: True/False on success
        """
        self.socket.settimeout(float(timeout))
        time_tries = 0
        while True:
            try:
                msg = self.socket.recv(buffer)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    print("Connection timed out, continuing.")
                    time_tries += 1
                    if time_tries > timeout_limit:
                        print("Timeout limit reached, closing connection")
                        return False
                    continue
                else:
                    print(e)
                    return False
            except socket.error as e:
                print(e)
                break
            else:
                if len(msg) == 0:
                    print("Orderly shutdown on server end")
                    return True
                else:
                    self._received_data.append(base64.b64decode(zlib.decompress(msg)))

    def received_data(self):
        """
        Method returns the last data received
        :return: data from remote host
        """
        return self._received_data

    def print_received_data(self):
        """
        Method prints out all data received from remote host
        :return: None
        """
        for ln in self._received_data:
            print(ln)

    def do_job(self):
        """
        Method converts raw data into usable data for the client process to work with
        :return: data for client process to work with
        """
        job_list = list()
        for item in self._received_data:
            if 'job' in str(item):
                print("Job Request Received, Starting work!\t{}".format((str(item))))
                job_list.append("{}".format(str(item).strip("'").split(" ")[1]))
        print(job_list)
        return job_list


if __name__ == "__main__":
    connections = []
    server_ip = config_manager.get_global("server_ip")
    server_port = int(config_manager.get_global("server_port"))
    for i in range(1):
        connections.append(ClientServer())
        connections[-1].connect(server_ip, server_port)
        connections[-1].send("get work")
        connections[-1].receive()
        connections[-1].print_received_data()
        connections[-1].do_job()
        connections[-1].close()
