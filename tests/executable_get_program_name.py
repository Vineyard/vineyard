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
    verbose = False
    if '--verbose' or '-v' in sys.argv:
        import pprint
        verbose = True
        try: sys.argv.pop(sys.argv.index('--verbose'))
        except ValueError: pass
        try: sys.argv.pop(sys.argv.index('-'))
        except ValueError: pass

    for exe in sys.argv[1:]:
        full_info = ''
        if verbose:
            full_info = []
            version_info = wine.binary.windows_executable(exe).get_version_fast()
            if 'ProductName' in version_info:
                full_info.append(('ProductName', version_info['ProductName']))
            if 'FileDescription' in version_info:
                full_info.append(('FileDescription', version_info['FileDescription']))
            if 'Comments' in version_info:
                full_info.append(('Comments', version_info['Comments']))
            full_info = '\t{0}\n{1}'.format('\n\t'.join([
                'Tried \'{0}\' : \'{1}\''.format(i[0], i[1])
                for i in full_info
            ]), pprint.pformat(version_info))

        print("{exe}:\n{full_info}\t{name}\n".format(
            exe = exe,
            full_info = full_info,
            name = wine.util.get_program_name(exe)
        ))
else:
    print("No file path given.")
    exit(1)

