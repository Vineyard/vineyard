#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Allow font antialiasing'),
            settings_key = 'direct3d-antialiasing',
            get_function = self._get_function,
            set_function = self._set_function)
        self.set_tooltip_text(_(
            "Enable or disable smooth edges on fonts." +
            "\n\n" +
            "Disabling this will force all programs to not use font anti-aliasing, " +
            "even if they ask for it."
        ))
    
    def _get_function(self):
        return not wine.graphics.get_antialiasing_disabled()
    
    def _set_function(self, value):
        return wine.graphics.set_antialiasing_disabled(not value)
