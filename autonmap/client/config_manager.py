#!/usr/bin/env python3

import configparser
from os import makedirs
from os.path import join, expanduser

"""
This module handles the config files for the client processes, it also
contains several functions which preform various tasks on teh config file.
"""

_user_home = expanduser('~')
_base = join(_user_home, "autonmap")

configFile = join(_base, "settings.ini")

# TODO: need to clean up

try:
    with open(configFile, "r") as FILE:
        pass
except FileNotFoundError:
    # Tell the user that the config file was not found  so a default is being created
    # host to scan and scanned host are stored in txt for simplicity might be subject to change

    defaultConfigFile = {
        "Time_Settings": {
            "Max_Timeout_Sec": 20.0
        },
        "Base_Folder": {
            "autonmap": _base
        },
        "known_folders": {
            "Data": join(_base, "data")
        },
        "Data_Path_Settings": {
            "Hosts_To_Scan": "hostToScan.txt",
            "Host_Scanned": "scannedHosts.txt",
            "Options": "options.txt"
        },
        "Scan_Data": {
            "File_Number": 0,
            "MAX_WORKERS": 10,
            "max_host_search": 20
        },
        "NMAP_MASTER": {
            "Argument": ' -n --max-retries 2 --max-rtt-timeout 800ms --min_parallelism 50 --max_parallelism 700'
        },
        "GLOBAL_SETTINGS": {
            "debug": False,
            "server_ip": "40.74.255.187",
            "server_port": 12990,
            "scantime-hours": 3,
        },
        "CLIENT_COMMANDS": {
            "request_job": "get work"
        }
    }

    try:
        makedirs(join(defaultConfigFile['Base_Folder']['autonmap']), mode=0o777)
    except FileExistsError:
        pass
    for fl in defaultConfigFile['known_folders']:
        try:
            makedirs(defaultConfigFile['known_folders'][fl], mode=0o777)
        except FileExistsError:
            pass

    with open(configFile, "w+") as FILE:
        tempConfig = configparser.ConfigParser()
        for header in defaultConfigFile.keys():
            tempConfig.add_section("%s" % header)
            for option in defaultConfigFile[header].keys():
                tempConfig.set(header, option, str(defaultConfigFile[header][option]))
        tempConfig.write(FILE)
finally:
    config = configparser.ConfigParser()
    config.read(configFile)


def config_selection_map(file, section=None):
    dict1 = {}
    if section is not None:
        options = file.options(section)
        for opt in options:
            try:
                dict1[opt] = file.get(section, opt)
                if dict1[opt] == -1:
                    print("skip: %s" % opt)
            except Exception as r:
                print("Exception on %s\n%s" % (opt, r))
    else:
        for section_ in config:
            if section_ != "DEFAULT":
                dict1[section_] = dict()
                for opt in config.options(section_):
                    dict1[section_][opt] = config[section_][opt]
    return dict1


def get_config():
    """
    Function returns the config file as a raw config parser object
    :return: configparser obj
    """
    return config


def get_base():
    """
    Function returns the base folder location for the program
    :return: str of base folder location
    """
    return get_config()['Base_Folder']['autonmap']


def get_all_folder_paths():
    """
    Function returns all know folder locations other than the base location folder
    :return: list(str) of all know folders to the program
    """
    folders = []
    for opt in config["known_folders"]:
        folders.append(config["known_folders"][opt])
    return folders


def get_folder_path(opt):
    """
    Function gets the folder path for a known folder name
    :param opt: folder to get location of
    :return: folder location
    """
    for opt in config["known_folders"]:
        if opt.lower() == opt:
            return config["known_folders"][opt]


def get_timeout():
    return config["Time_Settings"]['Max_Timeout_Sec'.lower()]


def file_settings(opt):
    """
    Function gets the file setting
    :param opt: Setting to look for
    :return: setting
    """
    for opt in config["Data_Path_Settings"]:
        if opt.lower() == opt:
            return config["Data_Path_Settings"][opt]


def get_scan_data(opt):
    """
    Function gets the scan option
    :param opt: option to look for
    :return: scan option
    """
    try:
        return config["Scan_Data"][opt.lower()]
    except:
        return False


def get_nmap_arguments():
    """
    Function returns the master nmap option
    :return: nmap options
    """
    return config['NMAP_MASTER']['Argument'.lower()]


def get_global(setting):
    """
    Function gets the global setting asked for if possible
    :param setting: setting to look for
    :return: setting
    """
    try:
        return config['GLOBAL_SETTINGS'][setting.lower()]
    except KeyError:
        return False


def get_client_commands(opt):
    try:
        return config['CLIENT_COMMANDS'][opt.lower()]
    except KeyError:
        return False


if __name__ == "__main__":
    print(config_selection_map(config))
