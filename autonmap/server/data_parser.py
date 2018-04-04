#!/usr/bin/env python3

from libnmap.parser import NmapParser


def parse(data):
    try:
        return NmapParser.parse_fromstring(data, incomplete=True)
    except:
        return NmapParser.parse_fromstring(data)
