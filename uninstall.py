#!/usr/bin/env python

"""
    Created by cengen on 9/21/17.
"""

import os.path

if __name__ == "__main__":
    print("Removing all files created by Autonmap")
    file_locations = ["/tmp/autonmap.log", "/root/autonmap", "~/autonmap"]
    for item in file_locations:
        print("Removing {}".format(item))
        try:
            os.remove(item)
        except:
            try:
                os.rmdir(item)
            except:
                try:
                    import shutil
                    shutil.rmtree(item)
                except:
                    print("Unable to remove {}".format(item))
    print("Removing AutoNmap Service")
    from subprocess import Popen
    Popen(["sudo", "bash", "uninstall.sh"])
    print("Finished Cleaning up files from AutoNmap")

