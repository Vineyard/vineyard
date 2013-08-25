#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import page
from vineyard.widgets import libraries_overrides

id = 'libraries'
position = 0.4

class Page(page.VineyardPage):
    def __init__(self, dev=False):
        page.VineyardPage.__init__(self,
            name = _("Libraries"),
            icon = 'document-properties',
            widgets = [
                libraries_overrides
            ])
