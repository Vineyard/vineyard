#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#

import crashhandler
import async
from common import *
import subprocess

SHARED_FILES_PATH = get_shared_files_path()

import wine
import widgets
import pages as _pages
from gtkwidgets import *

pages = [
    i for i in
        [ eval('_pages.%s' % i) for i in dir(_pages) if not i.startswith('_') ]
    if 'id' in dir(i)
]

#SimpleList = simplelist.SimpleList

def open_help():
    subprocess.Popen(['yelp', '%s/docs' % SHARED_FILES_PATH], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
