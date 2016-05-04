#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import common
import registry
import subprocess

OFFSCREEN_RENDERING_MODES = ['fbo', 'backbuffer', 'pbuffer']
OFFSCREEN_RENDERING_MODES_DEPRECATED = []

if common.VERSION_MAJOR >= 1 and common.VERSION_MINOR >= 2:
    OFFSCREEN_RENDERING_MODES.remove('pbuffer')
    OFFSCREEN_RENDERING_MODES_DEPRECATED.append('pbuffer')

def get_screen_dpi():
    if 'graphics-screen-dpi' in CACHE:
        return CACHE['graphics-screen-dpi']

    settings = registry.get('HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Hardware Profiles\\Current\\Software\\Fonts', quiet=True)
    if "LowPixels" in settings:
        return int(settings["LowPixels"], 16)
    else:
        return 96

def set_screen_dpi(value):
    dword = 'dword:000000'+hex(int(value))[2:]
    registry.set({'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Hardware Profiles\\Current\\Software\\Fonts': {"LogPixels": dword}})

def get_vertex_shader(program=None):
    if 'graphics-vertex-shader' in CACHE:
        return CACHE['graphics-vertex-shader']

    if program:
        settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\Direct3D' % program, quiet=True)
    else:
        settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Direct3D', quiet=True)
    if "VertexShaderMode" in settings:
        return False
    else:
        return True

def set_vertex_shader(value, program=None):
    if value == True or type(value) == type(str) and value.lower() == "hardware":
        value = None
    else:
        value = "disabled"
    if program:
        path = 'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\Direct3D' % program
    else:
        path = 'HKEY_CURRENT_USER\\Software\\Wine\\Direct3D'

    registry.set({path: {"VertexShaderMode": value}})

def get_pixel_shader(program=None):
    if 'graphics-pixel-shader' in CACHE:
        return CACHE['graphics-pixel-shader']

    if program:
        settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\Direct3D' % program, quiet=True)
    else:
        settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Direct3D', quiet=True)
    if "PixelShaderMode" in settings:
        return False
    else:
        return True

def set_pixel_shader(value, program=None):
    if value == True or type(value) == type(str) and value.lower() == "hardware":
        value = None
    else:
        value = "disabled"
    if program:
        path = 'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\Direct3D' % program
    else:
        path = 'HKEY_CURRENT_USER\\Software\\Wine\\Direct3D'

    registry.set({path: {"PixelShaderMode": value}})

def get_font_antialiasing():
    if 'graphics-font-antialiasing' in CACHE:
        return CACHE['graphics-font-antialiasing']

    settings = registry.get('HKEY_CURRENT_USER\\Control Panel\\Desktop')
    return 'FontSmoothing' in settings and settings['FontSmoothing'] == "2"

def set_font_antialiasing(value):
    if value:
        reg = {
            "FontSmoothing": 2,
            "FontSmoothingType": "dword:00000002",
            "FontSmoothingGamma": "dword:00000578",
            "FontSmoothingOrientation": "dword:00000001"
        }
    else:
        reg = {
            "FontSmoothing": None,
            "FontSmoothingType": None,
            "FontSmoothingGamma": None,
            "FontSmoothingOrientation": None
        }

    registry.set({'HKEY_CURRENT_USER\\Control Panel\\Desktop': reg})

def check_3d_support():
    """
        Check if the system has support for direct rendering
        Returns True or False
    """
    result = common.pipe([["glxinfo"], ["grep", "direct rendering"]])
    if "y" in result.split(':')[1].lower():
        return True
    else:
        return False

def get_antialiasing_disabled():
    if 'graphics-antialiasing-disabled' in CACHE:
        return CACHE['graphics-antialiasing-disabled']

    settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\X11 Driver')
    if (
        "ClientSideAntiAliasWithRender" in settings and
        "ClientSideAntiAliasWithCore" in settings and
        settings['ClientSideAntiAliasWithRender'].lower() == 'n' and
        settings['ClientSideAntiAliasWithCore'].lower() == 'n'
    ):
        return True
    else:
        return False

def set_antialiasing_disabled(value):
    if value:
        value = "N"
    else:
        value = None

    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\X11 Driver': {
        "ClientSideAntiAliasWithRender": value,
        "ClientSideAntiAliasWithCore": value
    }})

def get_video_memory_size():
    if 'graphics-video-memory-size' in CACHE:
        return CACHE['graphics-video-memory-size']

    settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Direct3D')
    if 'VideoMemorySize' in settings:
        try:
            return int(settings['VideoMemorySize'])
        except ValueError:
            return None
    else:
        return None

def set_video_memory_size(value):
    if value != None and type(value) != type(1):
        raise ValueError("type of value should be None or int")
    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Direct3D': {
        'VideoMemorySize': value
    }})

def get_offscreen_rendering_mode():
    if 'graphics-offscreen-rendering-mode' in CACHE:
        return CACHE['graphics-offscreen-rendering-mode']

    settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Direct3D')
    if 'OffscreenRenderingMode' in settings:
        return settings['OffscreenRenderingMode']
    else:
        if (
            common.VERSION_MAJOR >= 1 and
            common.VERSION_MINOR >= 1 and
            common.VERSION_MICRO >= 23
        ):
            return 'fbo'
        else:
            return 'backbuffer'

def set_offscreen_rendering_mode(mode):
    if mode != None:
        mode = mode.lower()
        if mode in OFFSCREEN_RENDERING_MODES_DEPRECATED:
            raise DeprecationWarning("%s is deprecated. Mode should be %s" % (
                mode, common.list_to_english_or(OFFSCREEN_RENDERING_MODES)
            ))
        elif mode not in OFFSCREEN_RENDERING_MODES:
            raise ValueError("mode should be %s" % (
                common.list_to_english_or(OFFSCREEN_RENDERING_MODES)
            ))
    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Direct3D': {
        'OffscreenRenderingMode': mode
    }})

@common.read_cache('graphics-allow-multisample')
def get_allow_multisampling():
    settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Direct3D')
    try:
        return settings['Multisampling'].lower() == 'enabled'
    except (KeyError, SyntaxError):
        return False

@common.write_cache('graphics-allow-multisample')
def set_allow_multisampling(value):
    value = common.value_as_bool(value)
    if value == None:
        raise ValueError("type of value should something convertable to a boolean")
    elif value == True:
        value = "enabled"
    else:
        value = None
    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Direct3D': {
        'Multisampling': value
    }})
    return value, True

def set_allow_xrandr(value):
    value = common.value_as_bool(value)
    if value == None:
        raise ValueError("type of value should something convertable to a boolean")
    elif value == True:
        value = 'y'
    else:
        value = 'n'

    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\X11 Driver': {
        'UseXRandR': value
    }})

def get_allow_xrandr():
    settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\X11 Driver')
    try:
        return settings['UseXRandR'].lower() == 'y'
    except (KeyError, SyntaxError):
        # Default is True
        return True

def get_mouse_warp():
    if 'xinput-mouse-warp' in CACHE:
        return CACHE['xinput-mouse-warp']

    settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\DirectInput', quiet=True)
    value = 'enable' # Default value
    if 'MouseWarpOverride' in settings:
        if type(settings['MouseWarpOverride']) in (str, unicode):
            if settings['MouseWarpOverride'].lower() in ('enable', 'disable', 'force'):
                value = settings['MouseWarpOverride'].lower()
    CACHE['xinput-mouse-warp'] = value
    return value

def set_mouse_warp(state='enable'):
    reg_state = 'enable' # Default value
    if state in ('enable', 'disable', 'force'):
        reg_state = state
    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DirectInput': {'MouseWarpOverride': reg_state}})
    CACHE['xinput-mouse-warp'] = reg_state

def get_csmt():
    if common.ENV.get('WINE_SUPPORTS_CSMT') == 'true':
        if common.ENV.get('WINE_SUPPORTS_CSMT_TYPE') == 'dll':
            dll_overrides = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\DllRedirects')
            try:
                return dll_overrides['wined3d'] == 'wined3d-csmt.dll'
            except (KeyError, SyntaxError):
                return False
        else:
            direct3d_settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Direct3D')
            try:
                return direct3d_settings['CSMT'] == 'enabled'
            except (KeyError, SyntaxError):
                return False
    else:
        return None

def set_csmt(value, program=None):
    value = common.value_as_bool(value)
    if value == None:
        raise ValueError("type of value should something convertable to a boolean")
    elif value == True:
        value = 'enabled'
    else:
        value = 'disabled'
        
    if common.ENV.get('WINE_SUPPORTS_CSMT') == 'true':
        if common.ENV.get('WINE_SUPPORTS_CSMT_TYPE') == 'dll':
            if value == 'enabled':
                value = 'wined3d-csmt.dll'
            else:
                value = None
            if program:
                registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DllRedirects' % program: {'wined3d': value}})
            else:
                registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DllRedirects': {'wined3d': value}})
        else:
            if program:
                registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\Direct3D' % program: {'CSMT': value}})
            else:
                registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Direct3D': {'CSMT': value}})
    else:
        return None

def set_dxva2_vaapi(value, program=None):
    value = common.value_as_bool(value)
    if value == None:
        raise ValueError("type of value should something convertable to a boolean")
    elif value == True:
        value = 'va'
    else:
        value = None

    if program:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DXVA2' % program: {'backend': value}})
    else:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DXVA2': {'backend': value}})

def get_dxva2_vaapi():
    if common.ENV.get('WINE_SUPPORTS_DXVA2_VAAPI') == 'true':
        settings = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\DXVA2')
        try:
            return settings['backend'].lower() == 'va'
        except (KeyError, SyntaxError):
            return False
    else:
        return None
