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
import pprint

def dict_diff(dict_a, dict_b):
    return dict([
        (key, dict_b.get(key, dict_a.get(key)))
        for key in set(dict_a.keys()+dict_b.keys())
        if (
            (key in dict_a and (not key in dict_b or dict_a[key] != dict_b[key])) or
            (key in dict_b and (not key in dict_a or dict_a[key] != dict_b[key]))
        )
    ])

if len(sys.argv) < 2:
    args = [
        'wine C:\\Program Files\\IExplorer\\iexplorer.exe',
        'wine "C:\\Program Files\\IExplorer\\iexplorer.exe"',
        'wine \'C:\\Program Files\\IExplorer\\iexplorer.exe\'',
        'wine "$WINEPREFIX/drive_c/Program Files/IExplorer/iexplorer.exe\"',
        'env WINEDEBUG= wine regedit.exe',
        'start "c:\\Windows\\Profiles\\All Users\\Start Menu\\Programs\\WinRAR/WinRAR.lnk"'
    ]
else:
    args = sys.argv[1:]

for arg in args:
    print("{args}\n\nparses to:".format(
        args = arg
    ))
    result = wine.parse_command(arg)
    result['env'] = dict_diff(wine.common.ENV, result['env'])
    print('{0}\n\n'.format(result))
