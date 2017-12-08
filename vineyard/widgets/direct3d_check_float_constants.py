#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Check shader float constants'),
            settings_key = 'direct3d-check-float-constants',
            get_function = self._get_function,
            set_function = self._set_function)
        self._tooltip_text = _(
            "Check whether shader constants are outside the " +
            "valid constant range (0-255) and return 0,0 if they are." + 
            "\n\n" +
            "This issue can occur on NVIDIA drivers in a few games " +
            "(The Witcher, Grim Dawn, Might & Magic Heroes VI and " +
            "the King's Bounty games are known to be affected). " +
            "\n\n" +
            "If you are seeing polygons displayed oddly, enabling " +
            "this feature may help.\n" +
            "Note that it has a minor impact on framerate."
        )
        self._tooltip_text_unavailable = _("Not supported in this version of Wine.")
        self.set_tooltip_text(self._tooltip_text)
    
    def _get_function(self):
        return wine.graphics.get_check_float_constants()
    
    def _set_function(self, value):
        return wine.graphics.set_check_float_constants(value)
        
        self.settings[self.settings_key] = wine.graphics.get_check_float_constants()

    def fill_widgets(self):
        if self.settings[self.settings_key] == None:
            self.checkbutton.set_active(False)
            self.checkbutton.set_sensitive(False)
            self.set_tooltip_text(self._tooltip_text_unavailable)
        else:
            self.checkbutton.set_active( self.settings[self.settings_key] == True )
            self.checkbutton.set_sensitive(True)
            self.set_tooltip_text(self._tooltip_text)
        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))
