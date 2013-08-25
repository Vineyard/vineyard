#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Allow DirectX programs to capture the mouse'),
            settings_key = 'directx-capture-mouse',
            get_function = wine.windows.get_mouse_grab,
            set_function = wine.windows.set_mouse_grab)
