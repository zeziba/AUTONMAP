#!/usr/bin/env python3

from os.path import join
from sys import argv

from netaddr import IPAddress, IPNetwork
from netaddr.core import AddrFormatError

from autonmap.server import server_config


def add_ip(ipaddress):
    try:
        IPAddress(ipaddress)
    except ValueError:
        try:
            IPNetwork(ipaddress)
        except ValueError:
            print("Failed to enter in a good ip address")
            return False
    except AddrFormatError:
        print("Failed to enter in a good ip address")
        return False
    with open(join(server_config.get_base(), "work.txt"), "a+") as file:
        file.write("\n")
        file.write(ipaddress)


def get_ips():
    address = []
    with open(join(server_config.get_base(), "work.txt"), "a+") as file:
        for line in file:
            try:
                address.append(IPAddress(line.strip('\n')))
            except ValueError:
                try:
                    address.append(IPNetwork(line.strip('\n')))
                except ValueError:
                    pass
            except AddrFormatError:
                pass


def main():
    if len(argv) > 1:
        print("Adding ip address to file")
        add_ip(argv[1])
    else:
        print("Usage autonmap-work <ipaddress/subnet>")
        print(get_ips())


if __name__ == "__main__":
    main()
