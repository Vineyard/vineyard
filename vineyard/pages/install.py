#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import page
from vineyard.widgets import installers

id = 'install'
position = 0.99

class Page(page.VineyardPage):
    def __init__(self, dev=False):
        self.no_loading = True
        page.VineyardPage.__init__(self,
            name = _("Install"),
            icon = ['system-software-install', 'system-software-installer', 'system-software-update'],
            widgets = [
                installers
            ])
