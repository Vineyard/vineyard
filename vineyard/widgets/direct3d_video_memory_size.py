#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import gtk, widget, wine

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self)
        self.title = "Direct3D Video Memory size"
        self.settings_key = 'direct3d-video-memory-size'
        self.set_function = wine.graphics.set_video_memory_size
        self._build_interface()
    
    def _build_interface(self):
        self.table = gtk.Table(rows=2, columns=2, homogeneous=False)
        
        self.radiobutton_auto = gtk.RadioButton(label=_("Auto detected"))
        self.radiobutton_auto.set_alignment(0.0, 0.5)
        self.table.attach(self.radiobutton_auto, 0,1, 0,1, gtk.FILL|gtk.EXPAND,0, 0,0)
        
        self.radiobutton_absolute = gtk.RadioButton(label='%s: ' % _("Absolute in MB"), group=self.radiobutton_auto)
        self.radiobutton_absolute.set_alignment(0.0, 0.5)
        self.table.attach(self.radiobutton_absolute, 0,1, 1,2, gtk.FILL|gtk.EXPAND,0, 0,0)
        
        self.spinbutton = gtk.SpinButton(climb_rate=16.0, digits=0)
        self.spinbutton.set_numeric(True)
        self.spinbutton.get_adjustment().set_lower(1)
        self.spinbutton.get_adjustment().set_upper(262144) # 256 GB, this should hold for some time
        self.spinbutton.get_adjustment().set_step_increment(1)
        self.table.attach(self.spinbutton, 1,2, 1,2, gtk.FILL|gtk.EXPAND,0, 0,0)
        
        self.pack_start(self.table)
        self.show_all()
        
        self.radiobutton_auto.connect('toggled', self.radiobutton_auto_toggled)
        self.spinbutton.connect_after('value-changed', self.spinbutton_changed)
    
    def radiobutton_auto_toggled(self, radiobutton):
        if self.gobject.loading: return False
        
        self.settings[self.settings_key] = None if radiobutton.get_active() else self.spinbutton.get_value_as_int()
        self.gobject.emit('settings-changed', self.settings_key, self.set_function, (self.settings[self.settings_key],))
    
    def spinbutton_changed(self, spinbutton):
        if self.gobject.loading: return False
        
        self.radiobutton_absolute.set_active(True)
        self.settings[self.settings_key] = spinbutton.get_value_as_int()
        self.gobject.emit('settings-changed', self.settings_key, self.set_function, (self.settings[self.settings_key],))
    
    def load_settings(self):
        self.settings[self.settings_key] = wine.graphics.get_video_memory_size()
    
    def fill_widgets(self):
        if self.settings[self.settings_key] == None:
            self.radiobutton_auto.set_active(True)
        else:
            self.radiobutton_absolute.set_active(True)
            self.spinbutton.set_value(int(self.settings[self.settings_key]))
        
        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))
