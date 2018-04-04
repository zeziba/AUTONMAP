#!/usr/bin/env bash

echo "Greetings, this will finish the install of the autonamp program onto this device.";

python3 -m pip uninstall crontabs;

touch /tmp/autonmap.log

sudo chmod 777 /tmp/autonmap.log
