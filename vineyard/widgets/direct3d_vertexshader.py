#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Enable hardware Vertex Shader support'),
            settings_key = 'direct3d-vertexshader',
            get_function = wine.graphics.get_vertex_shader,
            set_function = wine.graphics.set_vertex_shader)
