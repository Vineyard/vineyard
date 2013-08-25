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
    import pprint
    for lnk in sys.argv[1:]:
        print("{lnk}:\n\t{info}\n".format(
            lnk = lnk,
            info = pprint.pformat(wine.binary.windows_link(lnk))
        ))
else:
    print("No path to .lnk file given.")
    exit(1)

