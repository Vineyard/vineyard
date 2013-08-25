#!/usr/bin/python
# -*- coding: utf-8 -*-
#

from wine import binary
from pprint import pprint

import os

for i in os.listdir('/home/cybolic/Downloads'):
    if i.lower().endswith('.exe'):
        print "Getting icon from", i
        p = binary.windows_executable('/home/cybolic/Downloads/{0}'.format(
            i
        ))
        p.get_icon(output = '/tmp/TEST-'+i+'.ico')
#p = binary.windows_executable('/home/cybolic/Downloads/derive_setup.exe')
#pprint(p.read_resource_directory_table('.rsrc'))
