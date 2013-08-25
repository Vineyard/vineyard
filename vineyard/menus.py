#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import xdg.Menu
import xdg.DesktopEntry

def get_menu(path = None, deep = True):
    menu = xdg.Menu.parse()
    
    if path == None:
        return get_menu_entries(menu)
    else:
        for entry in menu.getEntries():
            if isinstance(entry, xdg.Menu.Menu) and entry.getPath() == path:
                return get_menu_entries(entry)

def get_menu_entries(menu_obj):
    ret_dict = {}
    for entry in menu_obj.getEntries():
        if isinstance(entry, xdg.Menu.Menu):
            ret_dict[menu_obj.getPath()] = get_menu_entries(entry)
        elif isinstance(entry, xdg.Menu.MenuEntry):
            ret_dict[entry.DesktopFileID] = entry
    return ret_dict

show_menu(xdg.Menu.parse())
