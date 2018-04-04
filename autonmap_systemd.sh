#!/usr/bin/env bash

[Unit]
Description="Autonmap allows the user to host a server that gives tasks to clients"
#The service will wait for  networking and syslog
After=syslog.target network.target
#not necessary but if it conflicts with something - add it here (like chrony and ntp)
Conflicts=sendmail.service exim.service

[Service]
#The type could be different , depends on many things
Type=forking
#not necessary but if it uses pid file - describe it
PIDFile=/var/run/autonmap.pid
#EnvironmentFile=-/etc/sysconfig/network
#prerequisite (for example it has to remove the pid or check for lock file , etc
#ExecStartPre=-/usr/libexec/postfix/aliasesdb
#ExecStartPre=-/usr/libexec/postfix/chroot-update
#Necessary - it tells the system how to start the process
ExecStart=/usr/bin/autonmap server start
#if the service supports reload - tell system how to reload it
#ExecReload=/usr/bin/autonmap restart
#necessary - tells system how to stop the service
ExecStop=/usr/bin/autonmap server stop
#Automatic restart by systemd
Restart=on-failure
#Time for system to wait before restart
RestartSec=42s

[Install]
WantedBy=multi-user.target