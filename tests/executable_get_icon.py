#!/usr/bin/python
# -*- coding: utf-8 -*-
#
from __future__ import print_function

import sys, os

sys.path.insert(0, os.path.normpath(
    os.path.abspath(os.path.dirname(sys.argv[0]))+'/../'
))
import vineyard

SHARED_FILES_PATH = vineyard.get_shared_files_path()

import wine

if len(sys.argv) > 1:
    exe = wine.binary.windows_executable(sys.argv[1])
    icon = exe.get_icon()
    if not icon is None:
        with open('{0}/wine_test_executable_icon'.format(common.ENV['VINEYARDTMP']), 'w') as _file:
            _file.write(icon)
        os.system('display {0}/wine_test_executable_icon'.format(common.ENV['VINEYARDTMP']))
    else:
        print(exe.read_resource_directory_table())
else:
    print("No file path given.")
    exit(1)

