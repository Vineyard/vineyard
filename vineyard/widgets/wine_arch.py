#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# 
# ww_wineloader="/opt/wine-staging/bin/wine"
# ww_wineserver="/opt/wine-staging/bin/wineserver"
# ww_wine="/opt/wine-staging/bin/wine"
# ww_winearch="win32"

import gtk, glib, widget, wine
from vineyard import common

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self)
        self.title = _('Architecture')
        self.settings_key = 'wine-environment-arch'
        self._build_interface()
    
    def _build_interface(self):
        self.hbox = gtk.HBox()
        self.label = gtk.Label('%s: ' % self.title)
        self.hbox.pack_start(self.label, False, False)
        self.label_arch = gtk.Label('')
        self.hbox.pack_end(self.label_arch, False, False)
        self.pack_start(self.hbox, True, False)
        self.show_all()
    
    def load_settings(self):
        self.settings[self.settings_key] = wine.common.ENV['WINEARCH']
    
    def fill_widgets(self):
        if self.settings[self.settings_key] is None:
            self.hide()
        else:
            if self.settings[self.settings_key] == 'win64':
                self.label_arch.set_text(_("64-bit"))
            else:
                self.label_arch.set_text(_("32-bit"))
            self.show()
        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))
