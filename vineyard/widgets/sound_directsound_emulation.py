#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Use driver emulation'),
            settings_key = 'sound-directsound-emulation',
            get_function = wine.audio.get_driver_emulation,
            set_function = wine.audio.set_driver_emulation)
