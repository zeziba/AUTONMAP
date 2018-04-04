#!/usr/bin/env bash

echo "Removing autonmap from system."

echo "Removing any files in /root/autonmap"
sudo rm -rf /root/autonmap

echo "Removing any files in ~/autonmap"
sudo rm -rf ~/autonmap

echo "Killing all autonmap processes"
for pid in `ps -aux | grep auto | awk '{PRINT $2}'`;
do
    kill ${pid}
done

echo "Disableing all autonmap services"
sudo stop autonmap.service
sudo disable autonmap.service
sudo systemctl daemon-reload

echo "Files still exists@ /etc/systemd/system/autonmap.service"
echo "    /etc/systemd/system/autonmap.service"

echo "Uninstalling autonmap"
sudo python3.4 -m pip uninstall autonmap -y

echo "All attempts to remove autonmap exhausted. Autonmap should be removed now."