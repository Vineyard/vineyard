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
        self.title = _('Open Main Drive')
        self.icon = 'folder'
        self._build_interface()
    
    def _build_interface(self):
        self.button = common.button_new_with_image(self.icon, label=self.title, use_underline=False)
        self.pack_start(self.button)
        self.show_all()
        
        self.button.connect('clicked', self.button_clicked)
    
    def button_clicked(self, button):
        if self.gobject.loading: return False
        
        # Open the mapped dir of the first (in alphabetical order) drive
        try:
            mapping = wine.drives.get_main_drive(use_registry=False)['mapping']
            wine.util.run_command(["xdg-open", mapping])
        except:
            return False
