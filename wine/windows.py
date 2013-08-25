#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import registry
import _cache

CACHE = _cache.Cache()

def get_decorated():
    if 'windows-decorated' in CACHE:
        return CACHE['windows-decorated']

    settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\X11 Driver', quiet=True)
    if "Decorated" in settings and "n" in settings["Decorated"].lower():
        value = False
    else:
        value = True
    CACHE['windows-decorated'] = value
    return value

def set_decorated(state):
    if state:
        reg_state = "Y"
    else:
        reg_state = "N"
    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\X11 Driver': {"Decorated": reg_state}})
    CACHE['windows-decorated'] = (state == True)

def get_managed():
    if 'windows-managed' in CACHE:
        return CACHE['windows-managed']

    settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\X11 Driver', quiet=True)
    if "Managed" in settings and "n" in settings["Managed"].lower():
        value = False
    else:
        value = True
    CACHE['windows-managed'] = value
    return value

def set_managed(state):
    if state:
        reg_state = "Y"
    else:
        reg_state = "N"
    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\X11 Driver': {"Managed": reg_state}})
    CACHE['windows-managed'] = (state == True)

def get_mouse_grab():
    if 'windows-mouse-grab' in CACHE:
        return CACHE['windows-mouse-grab']

    settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\X11 Driver', quiet=True)
    if "DXGrab" in settings and "n" in settings["DXGrab"].lower():
        value = False
    else:
        value = True
    CACHE['windows-mouse-grab'] = value
    return value

def set_mouse_grab(state):
    if state:
        reg_state = "Y"
    else:
        reg_state = "N"
    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\X11 Driver': {"DXGrab": reg_state}})
    CACHE['windows-mouse-grab'] = (state == True)

