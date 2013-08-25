#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Allow switching resolution using XRandR'),
            settings_key = 'direct3d-antialiasing',
            get_function = self.__get_function,
            set_function = self.__set_function)
        self.set_tooltip_text(_(
            "Allow using the XRandR extension to change screen resolution." +
            "\n\n" +
            "If you see a lot of errors with \"X11DRV_XRandR_SetCurrentMode\" try disabling this."
        ))
    
    def __get_function(self):
        return wine.graphics.get_allow_xrandr()
    
    def __set_function(self, value):
        return wine.graphics.set_allow_xrandr(value)
