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
        settings = ['fbo', 'backbuffer', 'pbuffer']
        names = ['Frame Buffer', 'Back Buffer', 'Pixel buffer']
        
        # Add any legal settings that we don't know about
        for setting in wine.graphics.OFFSCREEN_RENDERING_MODES:
            if setting not in settings:
                settings.append(setting)
                names.append(setting)
        
        # Remove any settings that are now deprecated
        for index, setting in enumerate(settings):
            if setting in wine.graphics.OFFSCREEN_RENDERING_MODES_DEPRECATED:
                settings.pop(index)
                names.pop(index)
        
        # Use the values from our_names and append any extra setting values added above
        match_values = zip(names, settings)
        
        widget.VineyardWidgetComboBox.__init__(self,
            title = '%s:' % _('Render offscreen images using the'),
            values = names,
            match_values = match_values,
            settings_key = 'direct3d-offscreen-rendering',
            get_function = self._get_function,
            set_function = self._set_function)
        self.set_tooltip_text(_(
            "Some programs and games work better or faster with one setting, others with another." +
            "\n\n" +
            "If you are experiencing issues with the speed of 3D in a program or game, try changing this setting."
        ))
    
    def _get_function(self):
        value = wine.graphics.get_offscreen_rendering_mode()
        return value.lower()
    
    def _set_function(self, value):
        wine.graphics.set_offscreen_rendering_mode(value)
