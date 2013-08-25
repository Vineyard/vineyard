#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Enable hardware Pixel Shader support'),
            settings_key = 'direct3d-pixelshader',
            get_function = wine.graphics.get_pixel_shader,
            set_function = wine.graphics.set_pixel_shader)
