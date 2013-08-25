#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Show windows in the taskbar'),
            settings_key = 'windows-managed',
            get_function = wine.windows.get_managed,
            set_function = wine.windows.set_managed)
