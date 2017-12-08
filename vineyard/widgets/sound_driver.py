#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#

from __future__ import print_function

import operator
import widget, wine

class Widget(widget.VineyardWidgetComboBox):
    def __init__(self):
        """ Compile a list of the available audio drivers, our preferred first """
        our_drivers = ['ALSA', 'OSS', 'Jack', 'Pulse', 'NAS', 'CoreAudio', 'AudioIO']
        our_drivers_lowered = [ n.lower() for n in our_drivers ]

        drivers = []
        # Use only the drivers that are available on this system
        for driver in our_drivers:
            if driver.lower() in wine.audio.DRIVERS:
                drivers.append(driver)
        # Add drivers that weren't on our sorted list
        for driver in wine.audio.DRIVERS:
            if driver.lower() not in our_drivers_lowered:
                drivers.append(driver.capitalize())

        match_values = []
        for driver in drivers:
            if driver.lower() == 'pulse':
                match_values.append(('PulseAudio', 'pulse'))
            else:
                match_values.append((driver, driver.lower()))

        widget.VineyardWidgetComboBox.__init__(self,
            title = '%s:' % _('Driver'),
            values = [ name for (name, value) in match_values ],
            match_values = match_values,
            settings_key = 'sound-drivers',
            get_function = self._get_setting,
            set_function = self._set_setting)

    def _get_setting(self):
        try:
            driver = wine.audio.get_enabled_drivers()[0]
        except IndexError:
            driver = ''
        if len(driver.strip()):
            return driver
        else:
            return 'alsa'
    def _set_setting(self, driver):
        wine.audio.set_enabled_drivers([driver])
