#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import page
from vineyard.widgets import configuration_name, version, files_show_hidden

id = 'general'
position = 0.0

class Page(page.VineyardPage):
    def __init__(self, dev=False):
        page.VineyardPage.__init__(self,
            name = _("General"),
            icon = 'computer',
            widgets = [
                (_('Configuration Settings'), [
                    configuration_name
                ]),
                (_('Windows Version'), [
                    version
                ]),
                (_('Hidden Files'), [
                    files_show_hidden
                ])
            ])
