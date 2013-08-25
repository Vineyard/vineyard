#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetComboBox):
    def __init__(self):
        """ Compile a list of the available settings, our preferred first """
        settings = ['enable', 'force', 'disable']
        names = [_('Yes'), _('Yes, force it'), _('No')]

        match_values = zip(names, settings)

        widget.VineyardWidgetComboBox.__init__(self,
            title = '%s: ' % _('DirectInput programs can warp the mouse pointer'),
            values = names,
            match_values = match_values,
            settings_key = 'directinput-mouse-warp',
            get_function = wine.graphics.get_mouse_warp,
            set_function = wine.graphics.set_mouse_warp
        )
        self.set_tooltip_text(_(
            "Programs that use DirectInput often requires the " +
            "mouse pointer position to be translated to a relative position " +
            "instead of an absolute one, also called mouse warping." +
            "\n\n" +
            "If you are having problems with the mouse leaving the window or " +
            "seem to hit the screen edge in games, try setting this setting to "+
            "Force, if not, set according to your preference." +
            "\n\n" +
            "The default is Enabled"
        ))

    def __get_function(self):
        return wine.graphics.get_mouse_warp()

    def __set_function(self, value):
        wine.graphics.set_mouse_warp(value)

