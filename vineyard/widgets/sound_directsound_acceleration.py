#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import operator
import widget, wine

class Widget(widget.VineyardWidgetComboBox):
    def __init__(self):
        """ Compile a list of the available settings, our preferred first """
        our_settings = ['Full', 'Standard', 'Basic', 'Emulation']
        our_settings_lowered = [ n.lower() for n in our_settings ]
        
        settings = []
        # Use only the drivers that are available on this system
        for setting in our_settings:
            if setting.lower() in wine.audio.ACCELERATIONS:
                settings.append(setting)
        # Add drivers that weren't on our sorted list
        for setting in wine.audio.ACCELERATIONS:
            if setting.lower() not in our_settings_lowered:
                settings.append(setting.capitalize())
        
        match_values = [ (i, i.lower()) for i in settings ]
        
        widget.VineyardWidgetComboBox.__init__(self,
            title = '%s:' % _('Hardware acceleration'),
            values = settings,
            match_values = match_values,
            settings_key = 'sound-directsound-acceleration',
            get_function = self.__get_function,
            set_function = wine.audio.set_acceleration)
    
    def __get_function(self):
        value = wine.audio.get_acceleration()
        return value.lower()
