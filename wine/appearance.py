#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import os, util, shutil
import registry, util, common

USER_PREFERENCES_MASK = {
    'active window tracking':
        { 'bit':  0, 'default': 0 },
    'menu animation':
        { 'bit':  1, 'default': 1 },
    'combo box animation':
        { 'bit':  2, 'default': 1 },
    'list box smooth scrolling':
        { 'bit':  3, 'default': 1 },
    'gradient captions':
        { 'bit':  4, 'default': 1 },
    'keyboard cues':
        { 'bit':  5, 'default': 0 },
    'active window tracking Z order':
        { 'bit':  6, 'default': 0 },
    'hot tracking':
        { 'bit':  7, 'default': 1 },
    'menu fade':
        { 'bit':  9, 'default': 1 },
    'selection fade':
        { 'bit': 10, 'default': 1 },
    'tool tip animation':
        { 'bit': 11, 'default': 1 },
    'tool tip fade':
        { 'bit': 12, 'default': 1 },
    'cursor shadow':
        { 'bit': 13, 'default': 1 },
    'new menu style':
        { 'bit': 17, 'default': 0 },
    'ui effects':
        { 'bit': 31, 'default': 1 }
}

def _get_theme_file_from_name(theme_name):
    if os.path.isfile(theme_name):
        theme_file = theme_name
    else:
        theme_file = None
        for test_path in [
            util.wintounix(
                'C:\\Windows\\Resources\\Themes\\%(name)s\\%(name)s.msstyles' % {
                    'name': theme_name
                }
            ),
            util.wintounix(
                'C:\\Windows\\Resources\\Themes\\%s\\~.msstyles' % (
                    theme_name
                )
            )
        ]:
            if os.path.isfile(test_path):
                theme_file = test_path
        if theme_file == None:
            raise OSError, "Theme file couldn't be found, tried \"%s\"" % theme_file
    return theme_file

def get_theme_info(theme_or_file):
    if os.path.isfile(theme_or_file):
        file_name = theme_or_file
    else:
        file_name = _get_theme_file_from_name(theme_or_file)
    with open(file_name, 'r') as _file:
        theme_data = _file.read()
    #try:
    #    description = theme_data.
    from pprint import pprint
    try:
        info = theme_data.replace('\x00','').split('\n')[-2]
        info = info.split('\x05')[-1]

        name = (
            info.split('\x0f')[0].strip().encode('string_escape')
        ).split('\\x')[0].decode('string_escape')
        copyright = (((
                    info.split('\x0c')[-1]
                ).split('\x08')[-1]
            ).split('\x1e')[0].strip().encode('string_escape')
        ).split('\\x')[0].decode('string_escape')
        url = ((info.split('\x1e')[1]
            ).split('\x1b')[0].strip().encode('string_escape')
        ).split('\\x')[0].decode('string_escape')
    except IndexError:
        raise TypeError, "Couldn't parse info from theme file \"%s\"" % theme_or_file
    return {'name': name, 'copyright': copyright, 'url': url}

def list_themes():
    themes_path = util.wintounix('C:\\Windows\\Resources\\Themes\\')
    themes_list = {}
    if os.path.isdir(themes_path):
        for name in os.listdir(themes_path):
            try:
                info = get_theme_info(name)
                themes_list[name] = info
            except (TypeError, OSError):
                themes_list[name] = {
                    'name': name,
                    'description': '',
                    'copyright':''
                }
        return themes_list
    else:
        return {}

def set_theme(theme):
    theme_file = _get_theme_file_from_name(theme)
    theme_file = util.unixtowin(theme_file)
    return registry.set({
        ('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\'+
         'CurrentVersion\\ThemeManager'): {
            "DllName": util.string_escape_char(theme_file, '\\'),
            "ThemeActive": '1'
        }
    })

def get_theme():
    if registry.get(
        'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\'+
        'CurrentVersion\\ThemeManager',
        'ThemeActive'
    ):
        return registry.get(
            'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\'+
            'CurrentVersion\\ThemeManager',
            'DllName'
        )

def remove_theme(theme_name):
    theme_file = _get_theme_file_from_name(theme_name)
    os.remove(theme_file)

def _create_theme_dir(theme_name):
    path_full = util.wintounix('C:\\Windows\\resources\\themes\\{0}'.format(
        theme_name
    ))
    path_parts = path_full.split('/')
    path = path_parts[0]
    for path_part in path_parts[1:]:
        path = '/'.join([path, path_part])
        print(path)
        if not os.path.isdir(path):
            print("Does not exist, creating...")
            if path == path_parts[-1] and os.path.exists(path):
                print("Is theme path and already exists, moving")
                shutil.move(path, '%s-old' % path)
            os.mkdir(path)
    return path

def install_theme(theme_file):
    # FIXME: Add support for multi-theme packages
    # (/theme-1/theme-1.msstyles, /theme-2/theme-2.msstyles, ...)
    if not theme_file.lower().endswith('.msstyles'):
        file_names = util.archive_extract_file(
            theme_file,
            extract_file = '*.msstyles',
            destination_dir = '{tmppath}-theme-extract'.format(
                tmppath = common.ENV['VINEYARDTMP'])
        )
        theme = file_names[-1]
    else:
        theme = theme_file

    if theme.lower().endswith('.msstyles'):
        theme_name = '.'.join(os.path.basename(theme).split('.')[:-1])
        target_path = _create_theme_dir(theme_name)
        shutil.copy(theme, '%s/%s.msstyles' % (target_path, theme_name))
    else:
        raise TypeError, (
            "Couldn't recognise the file as a theme file "+
            "or an archive containing one: %s" % theme_file
        )

def set_user_style(style, state):
    if style not in USER_PREFERENCES_MASK:
        raise ValueError, (
            "Argument style should be one of "+
            common.list_to_english_or((
                '"{0}"'.format(i) for i in
                USER_PREFERENCES_MASK.keys()
            ))
        )

    mask = registry.get(
        'HKEY_CURRENT_USER\\Control Panel\\Desktop', 'UserPreferenceMask'
    )
    if mask:
        mask = common.bitfield(mask)
        mask[ USER_PREFERENCES_MASK[style]['bit'] ] = int(state)
        registry_value = mask.registry_value()
        registry.set({
            'HKEY_CURRENT_USER\\Control Panel\\Desktop': {
                'UserPreferenceMask': registry_value
            }
        })
    else:
        return False

def get_user_style(style):
    if style not in USER_PREFERENCES_MASK:
        raise ValueError, (
            "Argument style should be one of "+
            common.list_to_english_or((
                '"{0}"'.format(i) for i in
                USER_PREFERENCES_MASK.keys()
            ))
        )

    mask = registry.get(
        'HKEY_CURRENT_USER\\Control Panel\\Desktop', 'UserPreferenceMask'
    )
    if mask:
        mask = common.bitfield(mask)
        return bool(mask[ USER_PREFERENCES_MASK[style]['bit'] ])
    else:
        return bool(USER_PREFERENCES_MASK[style]['default'])

def set_menu_style(state=True):
    """If true use the newer flat style menus, else use old 3D style."""
    if type(state) in (str, unicode):
        state = (state == 'flat')
    set_user_style('new menu style', state)

def get_menu_style():
    """If true the newer flat style menus are used, else the old 3D style are."""
    return get_user_style('new menu style')



