#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import gtk, widget, wine

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self)
        self.title = _('Default bit depth')
        self.settings_key = 'sound-directsound-bitdepth'
        self.set_function = wine.audio.set_bit_depth
        self._build_interface()
    
    def _build_interface(self):
        self.table = gtk.Table(rows=2, columns=3, homogeneous=False)
        
        if self.title != None:
            self.label = gtk.Label(self.title)
            self.label.set_alignment(0.0, 0.5)
            self.table.attach(self.label, 0,1, 0,1, gtk.FILL|gtk.EXPAND,0, 0,0)
        self.radiobutton8 = gtk.RadioButton(label='8')
        self.table.attach(self.radiobutton8, 1,2, 0,1, 0,0, 6,0)
        self.radiobutton16 = gtk.RadioButton(label='16', group=self.radiobutton8)
        self.table.attach(self.radiobutton16, 2,3, 0,1, 0,0, 0,0)
        
        self.pack_start(self.table)
        self.show_all()
        
        self.radiobutton8.connect('toggled', self.radiobutton8_toggled,
            self.settings_key, self.set_function)
    
    def radiobutton8_toggled(self, radiobutton, settings_key, function):
        if self.gobject.loading: return False
        
        self.settings[settings_key] = '8' if radiobutton.get_active() else '16'
        self.gobject.emit('settings-changed', settings_key, function, (self.settings[settings_key],))
    
    def load_settings(self):
        self.settings[self.settings_key] = wine.audio.get_bit_depth()
    
    def fill_widgets(self):
        if self.settings[self.settings_key] == '8':
            self.radiobutton8.set_active(True)
        else:
            self.radiobutton16.set_active(True)
        
        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))
