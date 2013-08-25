#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Allow multisample anti-alias'),
            settings_key = 'direct3d-allow-multisampling',
            get_function = wine.graphics.get_allow_multisampling,
            set_function = wine.graphics.set_allow_multisampling)
        self.set_tooltip_text(_(
            "Multisample anti-aliasing (MSAA) is technique for doing full-screen anti-aliasing." +
            "\n\n" +
            "Some graphic drivers exhibit issues when this is enabled (mostly NVIDIA), " +
            "and there are known issues with using it together with the frame buffer " +
            "offscreen renderer, " +
            "for this reason this setting is disabled by default." +
            "\n\n" +
            "If this setting is enabled and you get GLXBadDrawable errors, try disabling it."
        ))

