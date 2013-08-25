#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import gobject, gtk, widget
import wine

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self, {'desktop': None})
        self._build_interface()

    def _build_interface(self):
        self.table = gtk.Table(rows=2, columns=1, homogeneous=False)

        self.checkbutton = gtk.CheckButton(_('Open program windows in a virtual desktop'))
        self.table.attach(self.checkbutton, 0,1, 0,1, gtk.FILL,0, 0,0)

        self.table_values = gtk.Table(rows=2, columns=3, homogeneous=False)
        self.table.attach(self.table_values, 0,1, 1,2, gtk.FILL,gtk.FILL, 0,0)

        self.label_desktop_width = gtk.Label(_('Desktop width: '))
        self.label_desktop_width.set_padding(24,0)
        self.label_desktop_width.set_alignment(0.0, 0.5)
        self.table_values.attach(self.label_desktop_width, 0,1, 0,1, gtk.FILL,0, 0,0)

        self.spinbutton_width = gtk.SpinButton(climb_rate=1.0)
        self.spinbutton_width.get_adjustment().set_all(1024.0, lower=0, upper=10000, step_increment=1, page_increment=10, page_size=0)
        self.table_values.attach(self.spinbutton_width, 1,2, 0,1, gtk.FILL,0, 0,0)

        self.label_desktop_width_pixels = gtk.Label(_('pixels'))
        self.label_desktop_width_pixels.set_padding(6,0)
        self.table_values.attach(self.label_desktop_width_pixels, 2,3, 0,1, gtk.FILL,0, 0,0)

        self.label_desktop_width = gtk.Label(_('Desktop height: '))
        self.label_desktop_width.set_padding(24,0)
        self.label_desktop_width.set_alignment(0.0, 0.5)
        self.table_values.attach(self.label_desktop_width, 0,1, 1,2, gtk.FILL,0, 0,0)

        self.spinbutton_height = gtk.SpinButton(climb_rate=1.0)
        self.spinbutton_height.get_adjustment().set_all(768.0, lower=0, upper=10000, step_increment=1, page_increment=10, page_size=0)
        self.table_values.attach(self.spinbutton_height, 1,2, 1,2, gtk.FILL,0, 0,0)

        self.label_desktop_height_pixels = gtk.Label(_('pixels'))
        self.label_desktop_height_pixels.set_padding(6,0)
        self.table_values.attach(self.label_desktop_height_pixels, 2,3, 1,2, gtk.FILL,0, 0,0)

        self.table.show_all()
        self.pack_start(self.table)

        self.checkbutton.connect('toggled', self._on_change)
        self.spinbutton_width.connect('value-changed', self._on_change)
        self.spinbutton_height.connect('value-changed', self._on_change)

    def fill_widgets(self):
        if self.settings['desktop'] == None:
            # Set width to 75% of the screen
            desktop_width = int(gtk.gdk.get_default_root_window().get_geometry()[2]*0.75)
            # Set height to 75% of the screen
            desktop_height = int(gtk.gdk.get_default_root_window().get_geometry()[3]*0.75)
        else:
            desktop_width = int(self.settings['desktop'][0])
            # Set height to 75% of the screen
            desktop_height = int(self.settings['desktop'][1])

        self.checkbutton.set_active(self.settings['desktop'] != None)
        self.table_values.set_sensitive(self.settings['desktop'] != None)
        self.spinbutton_width.set_value(desktop_width)
        self.spinbutton_height.set_value(desktop_height)

        self.gobject.emit('settings-loaded', 'virtual-desktop', (self.settings['desktop'],))

    """
        Signal handlers
    """

    def _on_change(self, widget = None):
        if self.gobject.loading: return False

        if self.checkbutton.get_active():
            self.table_values.set_sensitive(True)
            self.settings['desktop'] = (
                self.spinbutton_width.get_value_as_int(),
                self.spinbutton_height.get_value_as_int()
            )
        else:
            self.table_values.set_sensitive(False)
            self.settings['desktop'] = None
        print("Changed:", self.settings['desktop'])
        self.gobject.emit('settings-changed', 'virtual-desktop', self.save_settings, (self.settings['desktop'],))

    def load_settings(self):
        self.settings['desktop'] = wine.desktop.get()

    def save_settings(self, setting):
        if setting is None:
            wine.desktop.set(False)
        else:
            wine.desktop.set(True, setting)
