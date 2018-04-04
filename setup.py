#!/usr/bin/env python

"""
Sets up the system to use the autonmap program.
"""

from setuptools import setup
from setuptools.command.install import install
from subprocess import Popen


class PostInstallation(install):

    def run(self):
        print("Is this a client: {}/{}".format('y', 'n'))
        ans = input("Is this a client: {}/{}".format('y', 'n'))
        if ans.lower() == 'y':
            Popen(['sudo', 'bash', 'client_setup.sh'])
        else:
            Popen(['sudo', 'bash', 'setup.sh'])
        install.run(self)

setup(
    name="autonmap",
    version="1.2.2",
    description="This program contains and utilizes a plethora of scripts to check a target network for open ports."
                "\nAfter discovery of a network occurs, the data is transmitted to a database manager and logged.\n"
                "The program will then request a new workload from the task manager program and begin work on\n"
                "scanning a new network.",
    author="Charles Engen",
    platforms="Linux",
    author_email="owenengen@gmail.com",
    license="NONE",
    packages=['autonmap', 'autonmap/client', 'autonmap/server'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Network Technicians',
        'Topic :: NMAP',
        'License :: NONE',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires='>=3',

    keywords='automated nmap server/client',

    install_requires=['python-nmap', 'python-libnmap', 'netaddr', 'configparser', 'python-crontab', 'croniter'],

    entry_points={
        'console_scripts': [
            'autonmap = autonmap.__main__:main'
        ]
    },
    cmdclass={
        'install': PostInstallation,
    },
)
