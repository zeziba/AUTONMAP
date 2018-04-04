#!/usr/bin/env python

"""
    Created by cengen on 9/17/17.
"""

from sys import argv
from netaddr import IPNetwork, cidr_merge, cidr_exclude


def split(subnet, prefix, count=None):

    subnet_split = {IPNetwork(subnet)}

    for ip_subnet in sorted(subnet_split, key=lambda x: x.prefixlen, reverse=True):
        subnets = list(ip_subnet.subnet(int(prefix), count=int(count) if count is not None else count))
        if not subnets:
            continue
        subnet_split.remove(ip_subnet)
        subnet_split = subnet_split.union(set(cidr_exclude(ip_subnet, cidr_merge(subnets)[0])))
        return subnets


if __name__ == "__main__":
    output = "IP Subnet splitter\n\tUsage: " \
             "\n\t\tpython3 subnetsplit.py ipsubnet cidr_mask count=optional" \
             "\n\t\tpython3 subnetsplit.py 127.0.0.1/27 30" \
             "\n\t\tpython3 subnetsplit.py 127.0.0.1/27 30 6"

    def main(arg1, arg2, arg3=None):
        a = split(arg1, arg2, arg3)
        for i in a:
            print(i.ipv4())

    if len(argv) == 3:
        main(arg1=argv[1], arg2=argv[2])
    elif len(argv) == 4:
        main(arg1=argv[1], arg2=argv[2], arg3=argv[3])
    else:
        print(output)
