#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>
#
# NOTE:
# This file belongs in /usr/lib/nautilus/extensions-2.0/python/

import nautilus
import gtk
import os, subprocess
import wine

import gettext as _gettext
from locale import getdefaultlocale

SHARED_FILES_PATH = None
for path in [ os.path.sep.join(i.split(os.path.sep)[:-1]) for i in os.environ['PATH'].split(':') ]:
    if os.path.isdir( "%s/share/vineyard" % path):
        SHARED_FILES_PATH = "%s/share/vineyard" % path

APP_NAME = "vineyard"

languages = ( [getdefaultlocale()[0]] or [] )
if 'LANGUAGE' in os.environ:
    languages = os.environ['LANGUAGE'].split(':') + languages
elif 'LANG' in os.environ:
    languages = os.environ['LANG'].split(':') + languages

_gettext.bindtextdomain(APP_NAME, "%s/%s" % (SHARED_FILES_PATH, "locale"))
_gettext.textdomain(APP_NAME)

gettext = _gettext.translation(APP_NAME, "%s/%s" % (SHARED_FILES_PATH, "locale"), languages=languages, fallback=True)
_ = gettext.gettext

class LocationProviderVineyard(nautilus.LocationWidgetProvider):
    def __init__(self):
        pass

    def get_widget(self, uri, window):
        widget = BarWidget(self, uri)
        if widget.configuration is None:
            return None
        else:
            return widget

def configure(widget=None, configuration=None):
    try:
        if configuration == 'default':
            subprocess.Popen(
                ['vineyard-preferences']
            )
        else:
            subprocess.Popen(
                ['vineyard-preferences', '-c', configuration]
            )
    except:
        pass

def show_help(widget=None):
    subprocess.Popen(
        ['yelp', '{0}/docs'.format(SHARED_FILES_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

class BarWidget(gtk.HBox):
    def __init__(self, parent, uri):
        gtk.HBox.__init__(self)
        self._parent = parent

        path = '://'.join(uri.split('://')[1:])
        if (
            path == os.path.expanduser('~/.wine') or
            path.startswith(os.path.expanduser('~/.wine/'))
        ):
            configuration = 'default'
        else:
            configuration = wine.prefixes.get_prefixpath_from_filepath(path)
            if configuration is not None:
                configuration = configuration['WINEPREFIXNAME']
        self.configuration = configuration

        if configuration is not None:
            self.icon = gtk.Image()
            try:
                pixbuf = gtk.icon_theme_get_default().load_icon(
                    'vineyard',
                    32,
                    0)
                self.icon.set_from_pixbuf(pixbuf)
            except glib.GError:
                pass
            self.pack_start(self.icon, expand=False, fill=False, padding=4)

            if configuration == 'default':
                self.label = gtk.Label(
                    _('This directory is in the default Wine/Vineyard configuration')
                )
            else:
                self.label = gtk.Label(
                    _('This directory is in the Vineyard configuration <b>{0}</b>').format(
                        configuration
                    )
                )

            self.label.set_use_markup(True)
            self.label.set_alignment(0.0, 0.5)
            self.label.set_line_wrap(False)
            self.pack_start(self.label, expand=True, fill=True, padding=4)

            self.button_configure = gtk.Button(_('Configure'))
            self.button_configure.connect('clicked', configure, configuration)
            self.pack_end(self.button_configure, expand=False, fill=False, padding=4)

            self.button_help = gtk.Button()
            image = gtk.Image()
            try:
                pixbuf = self.render_icon(gtk.STOCK_HELP, gtk.ICON_SIZE_BUTTON)
                image.set_from_pixbuf(pixbuf)
            except glib.GError:
                pass
            self.button_help.add(image)
            self.button_help.connect('clicked', show_help)
            self.pack_end(self.button_help, expand=False, fill=False, padding=4)

            self.show_all()

    def __set_image_from_name(self, image, image_name):
        try:
            pixbuf = gtk.icon_theme_get_default().load_icon(image_name, 32, 0)
            image.set_from_pixbuf(pixbuf)
        except glib.GError:
            pass
