#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine

class Widget(widget.VineyardWidgetCheckButton):
    def __init__(self):
        widget.VineyardWidgetCheckButton.__init__(self,
            title = _('Show new flat style menus'),
            settings_key = 'graphics-new-menu-style',
            get_function = wine.appearance.get_menu_style,
            set_function = wine.appearance.set_menu_style)