#!/usr/bin/env python3

from getpass import getuser

from crontab import CronTab

from autonmap.client import config_manager

"""
This method adds cron tasks for the autonmap program to be run with the configured settings.
"""


def main():
    ccommand = '\n/usr/bin/python3 -m autonmap {} {}\n'.format('client', 'start')
    ccomment = 'Client Start'
    ctimer = config_manager.get_global('scantime-hours')  # hours

    cron_u = CronTab(user=getuser())

    foundc = False
    for j in cron_u:
        print(j)
        if ccomment in j.comment:
            j.hour.every(ctimer)
            foundc = True
            cron_u.write()

    if not foundc:
        jobc = cron_u.new(command=ccommand, comment=ccomment)
        jobc.setall('0 */{} * * *'.format(ctimer))
        cron_u.write()


if __name__ == "__main__":
    main()
