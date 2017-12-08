#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Use VAAPI for DXVA2 GPU decoding'),
            settings_key = 'direct3d-dxva2-vaapi',
            get_function = self._get_function,
            set_function = self._set_function)
        self._tooltip_text = _(
            "Use VAAPI as the backend for DXVA2 GPU decoding." +
            "\n\n" +
            "Enabling this experimental feature allows video decoding to be " +
            "performed by the GPU on compatible graphics cards." +
            "\n\n" +
            "Note: This may crash on Intel GPUs; NVIDIA GPUs are known to work well."
        )
        self._tooltip_text_unavailable = _("Not supported in this version of Wine.")
        self.set_tooltip_text(self._tooltip_text)
    
    def _get_function(self):
        return wine.graphics.get_dxva2_vaapi()
    
    def _set_function(self, value):
        return wine.graphics.set_dxva2_vaapi(value)
        
        self.settings[self.settings_key] = wine.graphics.get_dxva2_vaapi()

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
