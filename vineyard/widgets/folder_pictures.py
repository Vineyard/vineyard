#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine, gtk

class Widget(widget.VineyardWidgetFileChooserButton):
    def __init__(self):
        widget.VineyardWidgetFileChooserButton.__init__(self,
            title = '%s: ' % _('My Pictures'),
            settings_key = 'shellfolder-pictures',
            get_function = self._get_function,
            set_function = self._set_function,
            mode=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self.foldername = 'My Pictures'
    
    def _get_function(self):
        folder = wine.shellfolders.get(self.foldername)
        if folder == None:
            return wine.util.get_real_home()
        return folder
    
    def _set_function(self, value):
        return wine.shellfolders.set(self.foldername, value)
