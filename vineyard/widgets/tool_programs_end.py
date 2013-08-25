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
        self.title = _('Close all programs')
        self.icon = 'window-close'
        self.widget_should_expand = True
        self._build_interface()
    
    def _build_interface(self):
        self.button = common.button_new_with_image(self.icon, label=self.title, use_underline=False)
        self.pack_start(self.button)
        self.show_all()
        
        self.button.connect('clicked', self.button_clicked)
    
    def button_clicked(self, button):
        if self.gobject.loading: return False
        
        wine.prefixes.end_session()
