#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

from __future__ import print_function

import os, sys, string
import common
import logging as _logging

logging = _logging.getLogger("python-wine")
debug = logging.debug
error = logging.error

if not len(common.ENV['WINE']):
    print("ERROR: Couldn't locate WINE, please make sure it is installed and in your PATH.",
          file=sys.stderr)
    exit(1)


__modules = [
    'common',
    'registry',
    'util',
    'command',
    'monitor',
    'audio',
    'prefixes',
    'drives',
    'desktop',
    'graphics',
    'icons',
    'appearance',
    'appdb',
    'programs',
    'shellfolders',
    'libraries',
    'version',
    'windows',
    'winetricks'
]

RUNNING_PROGRAMS = {}

_openargs = []

import _cache
cache = _cache.Cache()

for module_name in __modules:
    # Load the module
    exec('import %s' % module_name)
    # Assign the module to a value in the local namespace
    _module = eval(module_name)
    # Set the global attributes of the module
    setattr(_module, 'CACHE', cache)

# Set up the Wine prefix paths
prefixes.use(None) # Same as using ~/.wine actually


from base import *

