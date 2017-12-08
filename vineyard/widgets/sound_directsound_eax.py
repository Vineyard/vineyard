#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Enable EAX support'),
            settings_key = 'sound-directsound-eax',
            get_function = self._get_function,
            set_function = self._set_function)
        self._tooltip_text = _(
            "Enable support for Environmental Audio Extensions." +
            "\n\n" +
            "Enabling this experimental feature emulates driver support for EAX " +
            "using software emulation. This enables (mostly older) games to have " +
            "audio effects, such as reverb or equalisation."
        )
        self._tooltip_text_unavailable = _("Not supported in this version of Wine.")
        self.set_tooltip_text(self._tooltip_text)
    
    def _get_function(self):
        return wine.audio.get_eax_support()
    
    def _set_function(self, value):
        return wine.audio.set_eax_support(value)
        
        self.settings[self.settings_key] = wine.audio.get_eax_support()

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
