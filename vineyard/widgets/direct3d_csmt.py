#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Use CSMT'),
            settings_key = 'direct3d-csmt',
            get_function = self.__get_function,
            set_function = self.__set_function)
        self.__tooltip_text = _(
            "Use command stream multi-threading for Direct3D calls." +
            "\n\n" +
            "Enabling this experimental feature allows calls to OpenGL to be made " +
            "in separate threads, similar to how Direct3D works on Windows.\n" +
            "This can give significant performance improvements and fix " +
            "flickering geometry in games, but may cause other issues."
        )
        self.__tooltip_text_unavailable = _("Not supported in this version of Wine.")
        self.set_tooltip_text(self.__tooltip_text)
    
    def __get_function(self):
        return wine.graphics.get_csmt()
    
    def __set_function(self, value):
        return wine.graphics.set_csmt(value)
        
        self.settings[self.settings_key] = wine.graphics.get_csmt()

    def fill_widgets(self):
        if self.settings[self.settings_key] == None:
            self.checkbutton.set_active(False)
            self.checkbutton.set_sensitive(False)
            self.set_tooltip_text(self.__tooltip_text_unavailable)
        else:
            self.checkbutton.set_active( self.settings[self.settings_key] == True )
            self.checkbutton.set_sensitive(True)
            self.set_tooltip_text(self.__tooltip_text)
        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))
