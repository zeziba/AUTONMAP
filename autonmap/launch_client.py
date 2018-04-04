#!/usr/bin/env python3

"""
This module interfaces with the client process to provide a layer of abstraction to the client process.
"""

from sys import argv

from autonmap.client import client


def main(arg):
    _client = client.Client()
    if arg == "start":
        _client.do_work()
    elif arg == 'stop':
        _client.stop()
    else:
        print("Usage: start|stop")


if __name__ == "__main__":
    __client = client.Client()
    if len(argv) > 1:
        if argv[1] == "start":
            __client.do_work()
        elif argv[1] == 'stop':
            __client.stop()
    else:
        print("Usage: start|stop")
