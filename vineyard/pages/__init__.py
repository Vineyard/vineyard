#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import os
# Import the pages in this file's directory
for page in os.listdir(os.path.dirname(__file__)):
    if page.endswith('.py') and page != '__init__.py' and page != 'page.py':
        exec('import %s' % '.'.join(page.split('.')[:-1]))
