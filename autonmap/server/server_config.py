#!/usr/bin/env python3

import configparser
from os.path import join, expanduser

_user_home = expanduser('~')
_base = join(_user_home, "autonmap")

configFile = join(_base, "server_settings.ini")

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
        "GLOBAL_SETTINGS": {
            "debug": False,
            "server_ip": "10.0.0.4",
            "server_port": 12990
        },
        "CLIENT_COMMANDS": {
            "request_job": "get work"
        }
    }

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
    return config


def get_timeout():
    return config["Time_Settings"]['Max_Timeout_Sec'.lower()]


def get_base():
    return get_config()['Base_Folder']['autonmap']


def get_all_folder_paths():
    folders = []
    for opt in config["known_folders"]:
        folders.append(config["known_folders"][opt])
    return folders


def get_folder_path(opt):
    for opt in config["known_folders"]:
        if opt.lower() == opt:
            return config["known_folders"][opt]


def get_client_commands(opt):
    try:
        return config['CLIENT_COMMANDS'][opt.lower()]
    except KeyError:
        return False


def get_global(setting):
    try:
        return config['GLOBAL_SETTINGS'][setting.lower()]
    except KeyError:
        return False


if __name__ == "__main__":
    print(config_selection_map(config))
