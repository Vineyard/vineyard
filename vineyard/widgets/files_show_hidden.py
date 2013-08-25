#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Display hidden files'),
            settings_key = 'files-show-hidden',
            get_function = wine.drives.get_show_dot_files,
            set_function = wine.drives.set_show_dot_files)
