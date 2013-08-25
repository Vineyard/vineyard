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
        self.title = _('Open a Terminal in this Configuration')
        self.icon = 'terminal'
        self._build_interface()

    def _build_interface(self):
        self.button = common.button_new_with_image(self.icon, label=self.title, use_underline=False)
        self.pack_start(self.button)
        self.show_all()

        self.button.connect('clicked', self.button_clicked)

    def button_clicked(self, button):
        if self.gobject.loading: return False

        conf_name = wine.prefixes.get_name()
        if conf_name == None:
            conf_name = _('Default')
        wine.util.open_terminal(configuration_name=conf_name)
