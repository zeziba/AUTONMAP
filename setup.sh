#!/usr/bin/env bash

echo "Greetings, this will finish the install of the autonamp program onto this device.";

python3 -m pip uninstall crontabs;

touch /tmp/autonmap.log

sudo chmod 777 /tmp/autonmap.log



BASEDIR=$(dirname "$0")

# debian based system using init

#cp $BASEDIR/autonmap.sh /etc/init.d/autonmap

#update-rc.d autonmap defaults

#update-rc.d autonmap enable


# centos system using systemd

cp ${BASEDIR}/autonmap.sh /etc/systemd/system/autonmap.service

cp ${BASEDIR}/autonmap_systemd.sh /etc/systemd/system/autonmap.service

systemctl daemon-reload

systemctl enable autonmap.service

systemctl start autonmap.service


