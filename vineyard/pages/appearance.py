#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import page
from vineyard.widgets import virtual_desktop, menu_style
from vineyard.widgets import windows_decorated, windows_managed, font_antialias
from vineyard.widgets import themes

id = 'appearance'
position = 0.1

class Page(page.VineyardPage):
    def __init__(self, dev=False):
        page.VineyardPage.__init__(self,
            name = _("Appearance"),
            icon = ['preferences-theme', 'preferences-desktop-theme'],
            pages = [
                (_('Windows'), [
                    (_('Appearance'), [
                        windows_decorated,
                        windows_managed,
                        font_antialias,
                        menu_style
                    ]),
                    (_('Behavior'), [
                        virtual_desktop
                    ])
                ]),
                #(_('Colors'), [
                #]),
                (_('Theme'), [
                    themes
                ])
            ])

