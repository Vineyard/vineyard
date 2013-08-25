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
        our_settings = ['48000', '44100', '22050', '16000', '11025', '8000']
        
        settings = []
        # Use only the drivers that are available on this system
        for setting in our_settings:
            if int(setting) in wine.audio.RATES:
                settings.append(setting)
        # Add drivers that weren't on our sorted list
        for setting in wine.audio.RATES:
            if str(setting) not in our_settings:
                settings.append(str(setting))
        
        match_values = [ (i, i) for i in settings ]
        
        widget.VineyardWidgetComboBox.__init__(self,
            title = '%s:' % _('Default sample rate'),
            values = settings,
            match_values = match_values,
            settings_key = 'sound-directsound-samplerate',
            get_function = wine.audio.get_sample_rate,
            set_function = wine.audio.set_sample_rate)
