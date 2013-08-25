#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#

import os, sys

if len(sys.argv) > 1 and sys.argv[1] == 'vineyard':
    os.system('./vineyard-preferences --create-profile')
else:
    import cProfile
    cProfile.run('import wine; wine.programs.list_from_registry()', '/tmp/python-wine-profile.tmp')
    import pstats
    p = pstats.Stats('/tmp/python-wine-profile.tmp')
    p.sort_stats('cumulative').print_stats()
