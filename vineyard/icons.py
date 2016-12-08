#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import gtk, glib
try:
    import gio
except ImportError:
    # Older systems might not have gio,
    # that's okay, we only use it to check why an icon fails to load.
    # Ff a system doesn't have gio, there will be no fallback icon
    pass
import wine
import logging

logger = logging.getLogger("Wine Preferences - Icons")
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical

def get_icon_pixbuf_from_program(program=None, executable=None, size=32, force_update=False):
    # Fill the programs listview
    icon = wine.programs.get_icon(
        program = program,
        executable = executable,
        force_update = force_update
    )
    #self.debug("Icon lookup for \"%s\" returns \"%s\"." % (info['name'], icon))
    if icon is not None:
        icon = wine.icons.convert(icon)
        #if wine.util.isTempIcon(icon):
        #       #self.debug("\tIcon is template, removing and looking up again...")
        #       os.remove(icon)
        #       icon = wine.programs.getIcon(program, force_update=force_update)
        if icon is not None:
            if type(icon) == list:
                """ Manual icon replacement for script files """
                if icon == ['text-x-generic'] and 'programexe' in program and program['programexe'].lower().endswith('.bat'):
                    icon = gtk.icon_theme_get_default().load_icon('text-x-script', size, 0)
                else:
                    for iconname in icon:
                        try:
                            icon = gtk.icon_theme_get_default().load_icon(iconname, size, 0)
                            break
                        except glib.GError:
                            continue
            else:
                try:
                    icon = gtk.gdk.pixbuf_new_from_file_at_size(icon, size,size)
                except glib.GError:
                    warning("Tried to read \"%s\" as an icon and failed." % icon)
                    icon = None
                    pass
    if icon is None:
        #self.debug("\tIcon lookup returned nothing.")
        try:
            try:
                icon = gtk.icon_theme_get_default().load_icon("application-x-ms-dos-executable", size, 0)
            except glib.GError, gio.Error:
                icon = gtk.icon_theme_get_default().load_icon("application-x-executable", size, 0)
        except:
            icon = None
            #self.debug("\tUsing template icon.")
    return icon

def readPixbufFromFile(filename, size=None, only_programs=False):
    icon_file = wine.programs.getIcon({'name': 'vineyard-filepreview', 'icon': filename}, force_update=True)
    if icon_file == None:
        return None
    else:
        try:
            if size == None:
                return gtk.gdk.pixbuf_new_from_file(icon_file)
            else:
                return gtk.gdk.pixbuf_new_from_file_at_size(icon_file, size,size)
        except glib.GError:
            return None
