#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import gtk, widget, wine
from vineyard import common

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self)
        self.title = _('Lowercase files and folders in Main Drive')
        self.tooltip = _('Since Windows does not differentiate between upper and lowercase file names, this could help with performance (especially when used with ciopfs)')
        self.icon = 'edit-find-replace'
        self._build_interface()
        self.button.set_sensitive(False)
    
    def _build_interface(self):
        self.button = common.button_new_with_image(self.icon, label=self.title, use_underline=False)
        self.button.set_tooltip_text(self.tooltip)
        self.pack_start(self.button)
        self.show_all()
        
        self.button.connect('clicked', self.button_clicked)
    
    def button_clicked(self, button):
        if self.gobject.loading: return False
        
        self.threading.run_in_thread(self._find_files, callback = self._find_files_done)
        print "Looking for files with uppercase filenames..."
    
    def _find_files(self):
        self.files = wine.util.find_uppercase_filenames()
    
    def _find_files_done(self, return_value):
        print "Found %s files:" % len(self.files)
        print '\n'.join([ '\t%s' % i for i in self.files ])
        #self.pulse.stop()
