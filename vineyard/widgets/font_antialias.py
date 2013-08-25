#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Smooth font edges (anti-alias)'),
            settings_key = 'graphics-font-antialias',
            get_function = wine.graphics.get_font_antialiasing,
            set_function = wine.graphics.set_font_antialiasing)
