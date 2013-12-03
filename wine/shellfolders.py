#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

from __future__ import print_function

import registry, util, common
import os, sys, subprocess

FOLDER_REG_NAMES = {
    'desktop': 'Desktop',
    'my documents': 'Personal',
    'my pictures': 'My Pictures',
    'my music': 'My Music',
    'my videos': 'My Videos'
}


def get(folder=None):
    """Get the path of the directory defined in "folder" (one of the keys in FOLDER_REG_NAMES)."""
    if folder == None:
        try:
            return CACHE['shellfolders']
        except KeyError:
            pass
    else:
        folder = ' '.join(( i.capitalize() for i in folder.split() ))
        try:
            folders = CACHE['shellfolders']
            return folders[folder]
        except KeyError:
            pass

    folders = {}
    """userpath = registry.get('HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Session Manager\\Environment', 'APPDATA')
    for foldername in ["Desktop", "My Documents", "My Pictures", "My Music", "My Videos"]:
        if userpath:
            folders[foldername] = os.path.realpath("%s/drive_c/%s/%s" % (common.ENV['WINEPREFIX'], "/".join(userpath[3:].split("\\")[:-1]), foldername))
        else:
            folders[foldername] = util.getRealHome()"""
    reg_folders = registry.get('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer', 'Shell Folders')
    for folder_name, reg_name in FOLDER_REG_NAMES.iteritems():
        try:
            folder_path = os.readlink(util.wintounix(reg_folders[reg_name]))
        except (KeyError, OSError):
            folder_path = util.getRealHome()

        folder_name = ' '.join(( i.capitalize() for i in folder_name.split() ))
        folders[folder_name] = folder_path
    CACHE['shellfolders'] = folders
    if folder == None:
        return folders
    else:
        try:
            return folders[folder]
        except KeyError:
            return None


def set(foldername, target):
    """Set the shellfolder "foldername" (one of the keys in FOLDER_REG_NAMES) to the directory "target"."""
    if foldername.lower() in FOLDER_REG_NAMES.keys():
        # Camelcase the folder
        #foldername = " ".join([ i.capitalize() for i in foldername.split(" ") ])
        #userpath = registry.get('HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Session Manager\\Environment', 'APPDATA')
        #folderpath = "%s/drive_c/%s/%s" % (common.ENV['WINEPREFIX'], "/".join(userpath[3:].split("\\")[:-1]), foldername)
        folder_path = registry.get('HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders', FOLDER_REG_NAMES[foldername.lower()])
        # If the registy folder path is a symlink from inside the configuration, change the symlink
        if isinstance(folder_path, basestring) and ('\\windows\\' or '\\users\\' in folder_path):
            folder_path = util.wintounix(folder_path)
            try:
                os.remove(folder_path)
            except OSError:
                try:
                    os.rmdir(folder_path)
                except OSError:
                    print("Skipping %s, there are files in the directory" % os.path.basename(folder_path), file=sys.stderr)
            os.symlink(target, folder_path)
        # If not, it refers to a real directory, don't mess with it, set the registry info instead
        else:
            folder_path = target
            registry.set({'HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders': {FOLDER_REG_NAMES[foldername.lower()]: folder_path}})
        try:
            folders = CACHE['shellfolders']
        except KeyError:
            folders = {}
        folders[foldername] = folder_path
        CACHE['shellfolders'] = folders


def setdefaults():
    """Set the shellfolder mappings to directories inside the configuration dir or, if it's default configuration, to matching folders in the user's home directory (using automap)."""
    HOME = util.get_real_home()
    #if HOME == common.ENV['HOME']:
    if common.ENV['WINEPREFIX'] == os.path.expanduser('~/.wine'):
        return automap()

    for folder_name in FOLDER_REG_NAMES.iterkeys():
        create_dir = "%s/%s" % (common.ENV['VINEYARD_DATA'], folder_name)
        if not os.path.exists(create_dir):
            if not os.path.exists(os.path.dirname(create_dir)):
                os.mkdir(os.path.dirname(create_dir))
            os.mkdir(create_dir)
        set(folder_name, create_dir)

def automap():
    """Map the shellfolders to matching folders in the user's home directory."""
    HOME = util.get_real_home()
    # Iterate the XDG User Dirs and set Wine's ShellFolders up to match, defaulting to $HOME if there is no matching XDG Dir
    for dirname in [('DESKTOP', 'Desktop'), ('DOCUMENTS', 'My Documents'), ('MUSIC', 'My Music'), ('PICTURES', 'My Pictures'), ('VIDEOS', 'My Videos')]:
        xdgdir = _get_xdg_dir(dirname[0])
        if xdgdir:
            set(dirname[1], xdgdir)
        else:
            # First try, fx. "$HOME/My Documents", then "$HOME/Documents" else just link to "$HOME"
            if os.path.exists("%s/%s" % ( HOME, dirname[0].capitalize() )):
                set(dirname[1], "%s/%s" % ( HOME, dirname[0].capitalize() ))
            elif os.path.exists("%s/%s" % ( HOME, dirname[1] )):
                set(dirname[1], "%s/%s" % ( HOME, dirname[1] ))
            else:
                set(dirname[1], HOME)


def _get_xdg_dir(name):
    HOME = util.get_real_home()
    lines = []
    for filename in ["$XDG_CONFIG_HOME/user-dirs.dirs", "%s/.config/user-dirs.dirs" %HOME]:
        if os.path.exists(os.path.expandvars(filename)):
            f = open(filename)
            lines = f.readlines()
            f.close()
            break
    for line in lines:
        if line.startswith('XDG_'+name.upper()):
            return os.path.normpath(os.path.expandvars(line.split('=')[1].strip()[1:-1]))
    return None
