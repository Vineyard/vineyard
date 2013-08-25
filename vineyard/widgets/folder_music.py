#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine, gtk

class Widget(widget.VineyardWidgetFileChooserButton):
    def __init__(self):
        widget.VineyardWidgetFileChooserButton.__init__(self,
            title = '%s: ' % _('My Music'),
            settings_key = 'shellfolder-music',
            get_function = self.__get_function,
            set_function = self.__set_function,
            mode=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        self.foldername = 'My Music'
    
    def __get_function(self):
        folder = wine.shellfolders.get(self.foldername)
        if folder == None:
            return wine.util.get_real_home()
        return folder
    
    def __set_function(self, value):
        return wine.shellfolders.set(self.foldername, value)
