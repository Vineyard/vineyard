#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import page
from vineyard.widgets import programs
from vineyard.widgets import programs_new

id = 'programs'
position = 0.9

class Page(page.VineyardPage):
    def __init__(self, dev=False):
        if dev:
            page.VineyardPage.__init__(self,
                name = _("Programs"),
                icon = 'package-x-generic',
                pages = [
                    (_('From Menu'), [
                        programs_new
                    ])
                ]
            )
        else:
            page.VineyardPage.__init__(self,
                name = _("Programs"),
                icon = 'package-x-generic',
                widgets = [
                    programs
                ]
            )
