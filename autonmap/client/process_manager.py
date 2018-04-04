#!/usr/bin/env python3
import traceback
from sys import argv, version_info
from sys import exit as sys_exit

try:
    assert version_info >= (3, 0)
except AssertionError:
    print("Python 3.2.0+ is required to run this script package")
    sys_exit(-1)

from libnmap.process import NmapProcess as NProcess
from libnmap.parser import NmapParser, NmapParserException
from os import mkdir, system
from os.path import join
from netaddr import IPNetwork, IPAddress, IPSet
import signal

from autonmap.client import known_ports as KNPORTS
from autonmap.client import config_manager
from autonmap.client.database_client import DatabaseManager

"""
This module is the process manager that interacts with nmap to preform network scans on a target host.
Using several scanning techniques and several layering methods to quickly and definitively find any open
ports in the network.
"""

__DEBUG__ = False if config_manager.get_global('debug') == 'False' else True


class SignalWatch:
    """
    This class is used to tell the process if there is a kill signal so that the child processes
    can be shut down if possible.
    """

    kill = False

    def __init__(self):
        signal.signal(signal.SIGINT, self._exit)
        signal.signal(signal.SIGTERM, self._exit)

    def _exit(self, signum, frame):
        self.kill = True


class ProcessManager:
    """
    Work with nmap process to create and manage threads of nmap scans.
    """

    def __init__(self):
        self.hosts_to_scan = {"high": set(), "med": set(), "low": set()}
        self._init_host_scan = []
        self._create_file_structure()
        self.max_workers = int(config_manager.get_scan_data("MAX_WORKERS"))  # add to config file
        self._file_number = 0
        self.options = config_manager.get_nmap_arguments()
        self.database = DatabaseManager()
        self.__max_host_scan = int(config_manager.get_scan_data("max_host_search"))
        self.__scan_options = []
        self._scanned_hosts = []
        self.exit = SignalWatch()

    def __load_options(self):
        try:
            with open(join(config_manager.get_base(), "options.txt"), "r") as file:
                for line in file:
                    self.__scan_options.append(line.strip("\n"))
            self.__scan_options = sorted(set(self.__scan_options))
        except FileNotFoundError:
            with open(join(config_manager.get_base(), "options.txt"), "w+") as file:
                op = ['-sT', '-sU', '-sN', '-sF']  # default options to be loaded
                for opt in op:
                    file.write("{}\n".format(opt))
            self.__load_options()

    def _add_host(self, level, ip_addr, subnet=31):
        """
        Adds a generator object to the host_to_scan to use to give nmap jobs
        :param level: The priority of the scan
        :param ip_addr: Address of the host
        :param subnet: if a subnet mask is needed
        :return: None
        """
        gen = IPSet(["{}/{}".format(ip_addr, subnet)])
        for _ip in gen:
            self.hosts_to_scan[level].add(_ip)

    def add_host(self, ip_addr):
        """
        This method adds a ip address to be scanned to the waiting jobs.
        :param ip_addr:
        :return:
        """
        self._init_host_scan.append(ip_addr)

    @classmethod
    def _create_file_structure(*cls):
        folders = config_manager.get_all_folder_paths()
        for path in folders:
            try:
                print("Creating folder @ {}".format(path))
                mkdir(path=path, mode=0o777)
            except FileExistsError:
                pass

    def to_file(self, data, filename=""):
        """
        Debug method which saves the data data to file for inspection
        :param data: data to be saved
        :param filename: file location
        :return: None
        """
        with open(filename if filename else "{}".format(join(config_manager.get_base(), "data",
                                                             "data/outfile%d.xml")) % self._file_number, "w+") as file:
            file.write(data)
        self._file_number += 1

    def run(self):
        """
        This is the mainloop of the process manager.

        It will go over the ip address given and preform an initial host discovery, after that it will run deeper
        level scans of the network starting with the hosts found in the first scan. It will then move onto the remaining
        hosts.
        :return: True/False/None based on if the process failed to complete
        """

        _exit = self.exit
        _is_empty = False
        _jobs = []

        _uncommon_ports = sorted(set(range(65535)) - KNPORTS.as_nums())
        _uncommon_ports = ["{}-{}".format(*i) if i[0] != str(i[1]) else i[0] for i in KNPORTS.group(_uncommon_ports)]

        try:
            self.database.open_db()
            self.__load_options()

            def job(item, opt_override=""):
                if type(item) is list:
                    ipv4 = NProcess(options=self.options if not opt_override else opt_override)
                    ipv6 = NProcess(options="{} {}".format("-6", self.options if not opt_override else opt_override))
                    ipv4.targets.pop()  # removes the default target list
                    ipv6.targets.pop()
                    for h_ip in item:
                        if h_ip.ipv4():
                            ipv4.targets.append(str(h_ip.ipv4()))
                        else:
                            ipv6.targets.append(str(h_ip.ipv6()))
                    if ipv4.targets:
                        _jobs.append(ipv4)
                        _jobs[-1].run_background()
                    if ipv6.targets:
                        _jobs.append(ipv6)
                        _jobs[-1].run_background()
                else:
                    if item.ipv4():
                        _jobs.append(
                            NProcess(str(item.ipv4()), options=self.options if not opt_override else opt_override))
                    else:
                        _jobs.append(NProcess(str(item.ipv6()), options="{} {}".
                                              format("-6", self.options if not opt_override else opt_override)))
                    _jobs[-1].run_background()

            def process_jobs():
                for ind, proc in enumerate(_jobs):
                    if proc.has_terminated():
                        if proc.rc != 0:
                            print("nmap scan failed: {0}".format(proc.stderr))
                        if __DEBUG__: self.to_file(proc.stdout)
                        try:
                            parsed = NmapParser.parse(proc.stdout)
                            if __DEBUG__: print(parsed.summary)
                            for host in parsed.hosts:
                                print("Saving {} to database.".format(host.address))
                                self.database.add_ip_scan(ipaddr=host.address, port_data=host.get_open_ports(),
                                                          e_time=parsed.elapsed, command=proc.command,
                                                          raw_data=host.get_dict(), _raw=proc.stdout)
                        except NmapParserException as e:
                            print("Exception raised while parsing scan: {0}".format(e.msg))
                        self.database.commit()
                        del _jobs[ind]
                        break

            # preform 1st level scan
            if __DEBUG__: print("Initial Scan")
            init_discovery = set()
            while self._init_host_scan:
                try:
                    _ip = IPNetwork(self._init_host_scan.pop())
                    self._scanned_hosts.append(_ip.ipv4() if _ip.ipv4 else _ip.ipv6)
                    if _ip.ipv4():
                        _h = NProcess(list("%s" % i for i in _ip.ipv4()), options="-sn")
                    else:
                        _h = NProcess(list("%s" % i for i in _ip.ipv6()), options="-sn -6")
                    _h.sudo_run()
                    _p = NmapParser.parse(_h.stdout)
                    for _host in _p.hosts:
                        if _host.is_up():
                            init_discovery.add(_host.ipv4 if _host.ipv4 else _host.ipv6)
                        else:
                            self._add_host("med", _host.ipv4 if _host.ipv4 else _host.ipv6, 32)
                except NmapParserException:
                    pass

            # preform 2nd level scan, will only be preformed on init hosts found
            if __DEBUG__: print("Secondary Scans")
            _knports = ",".join(
                ["{}-{}".format(*i) if i[0] != i[1] else str(i[0]) for i in KNPORTS.group(list(KNPORTS.as_nums()))])
            for _ip in init_discovery:
                for opt in self.__scan_options:
                    job(IPAddress(_ip), opt_override="{} -p {} {}".format(opt, _knports, self.options))

            # all code beyond this point will take a very long time to execute
            if __DEBUG__: print("Primary Scans")
            if __DEBUG__: print(self.hosts_to_scan)
            while 1:

                if _exit.kill:
                    for _index, _j in enumerate(_jobs):
                        _jobs[_index].stop()
                    return False

                if len(_jobs) < self.max_workers and not _is_empty:
                    ip_group = []
                    while len(ip_group) < self.__max_host_scan and not _is_empty:
                        try:
                            # job(self.hosts_to_scan['high'].pop())
                            ip_group.append(self.hosts_to_scan['high'].pop())
                        except KeyError as e1:
                            try:
                                # job(self.hosts_to_scan['med'].pop())
                                ip_group.append(self.hosts_to_scan['med'].pop())
                            except KeyError as e2:
                                try:
                                    # job(self.hosts_to_scan['low'].pop())
                                    ip_group.append(self.hosts_to_scan['low'].pop())
                                except KeyError as e3:
                                    _is_empty = True
                    for opt in self.__scan_options:
                        job(ip_group, opt_override="{} -p {} {}".format(opt, _knports, self.options))

                process_jobs()
                if len(_jobs) == 0:
                    break

        except Exception as error:
            print("Failed: {}\t {}\n Cleaning up processes".format(Exception, error))
            traceback.print_tb(error.__traceback__)
            for _index, _j in enumerate(_jobs):
                try:
                    _jobs[_index].stop()
                except Exception as err:
                    print("Failed to stop {}\t{}".format(Exception, err))
                    print("Killing all nmap process!")
                    system('killall -9 nmap')
                    system('killall -9 python')
                    system('killall -9 python3')
                    print("Killall command for nmap process sent")
                finally:
                    print("Job Failed with kill signal.")
            return False
        # Time to run the uncommon ports, this will take a HUGE amount of time
        print("Final Scan\nThis Scan will take a very long time\n")
        _jobs = []
        while self._scanned_hosts:
            __ip = self._scanned_hosts.pop()
            for opt in self.__scan_options:
                job(__ip, opt_override="{} -p {} {}".
                    format(opt, ",".join(_uncommon_ports), self.options))
        while 1:
            if _exit.kill:
                try:
                    for _index, _j in enumerate(_jobs):
                        _jobs[_index].stop()
                except PermissionError:
                    return False
                finally:
                    print("Job Failed with kill signal.")
                return False

            process_jobs()

            if len(_jobs) == 0:
                break

        self.database.close_db()


if __name__ == "__main__":
    process_manager = ProcessManager()
    if len(argv) > 1:
        for index, ip in enumerate(argv):
            if index > 0:
                process_manager.add_host(ip)
        process_manager.run()
    else:
        print("Usage: %s 127.0.0.0/30" % argv[0].split("/")[-1])
        print("Usage: %s 127.0.0.0/30 127.0.1.0/30" % argv[0].split("/")[-1])
        print("Additional commands can be entered into the argument file which is"
              " specified in the config.ini\n"
              "To scan the remaining ~64k ports it must be specified in the parameters(TODO)")
