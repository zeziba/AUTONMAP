#!/usr/bin/env python3

from os import walk
from os.path import dirname, join, realpath
from sys import argv

"""
This module is used to change the shebang line of the included .py files to match the system being used on.
"""

statement = "#!/usr/bin/env python{}\n"


def fix_file(filename, version):
    with open(filename, "r") as original:
        original.readline()
        data = original.read()
        with open(filename, "w") as modified:
            modified.write(statement.format(version) + data)


if __name__ == "__main__":
    if len(argv) > 2:
        if "fix" == argv[1]:
            for root, dirs, files in walk(dirname(realpath(__file__))):
                for file in files:
                    if file.endswith(".py"):
                        _f = join(root, file)
                        print("Updating {}".format(_f))
                        fix_file(_f, argv[2])
    else:
        print("Usage: python update_code.py {} {}".format("fix", "<VERSION>"))
        print("Usage: python update_code.py {} {}".format("fix", "3.6"))
