#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>
#
# NOTE:
# This file belongs in /usr/lib/nautilus/extensions-2.0/python/

from __future__ import print_function

print("Initializing Wine integration: Property page")

import urllib
import os, sys
import wine
import wine.binary

import gtk
import nautilus
import gettext as _gettext
from locale import getdefaultlocale

SUPPORTED_FORMATS = (
    'application/x-ms-dos-executable', 'application/x-msdos-program',
    'application/x-msdownload', 'application/exe', 'application/x-exe',
    'application/dos-exe', 'vms/exe', 'application/x-winexe',
    'application/msdos-windows', 'application/x-zip-compressed',
    'application/x-executable','application/x-msi',
    'application/x-win-lnk', 'application/x-ms-shortcut'
)
LINK_FORMATS = (
    'application/x-win-lnk', 'application/x-ms-shortcut'
)
SUPPORTED_FORMATS = tuple(list(SUPPORTED_FORMATS) + list(LINK_FORMATS))

SHARED_FILES_PATH = None
if os.path.isdir( "%s/locale" % os.path.abspath(os.path.dirname(sys.argv[0])) ):
    SHARED_FILES_PATH = os.path.abspath(os.path.dirname(sys.argv[0]))
else:
    for path in [ os.path.sep.join(i.split(os.path.sep)[:-1]) for i in os.environ['PATH'].split(':') ]:
        if os.path.isdir( "%s/share/vineyard" % path):
            SHARED_FILES_PATH = "%s/share/vineyard" % path

if SHARED_FILES_PATH == None:
    print("Something is wrong with the installation, can't find required files. Exiting.")
    exit(1)

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

class WinePropertyPage(nautilus.PropertyPageProvider):
    def __init__(self):
        pass

    def get_property_pages(self, files):
        self.files = filter(lambda f: f.get_uri_scheme() == 'file' and not f.is_directory() and f.get_mime_type() in SUPPORTED_FORMATS, files)

        if len(self.files) == 0:
            return

        # TODO: Support multiple files (is this even feasible?)
        mime_type = self.files[0].get_mime_type()
        filename = os.path.normpath(
            urllib.unquote(
                '://'.join(self.files[0].get_uri().split('://')[1:])
            )
        )

        if not os.access(filename, os.R_OK):
            return

        self.alignment = gtk.Alignment(xalign=0.0, yalign=0.0, xscale=1.0, yscale=1.0)
        self.alignment.set_padding(0, 0, 6, 6)
        self.table = gtk.Table(rows=2, columns=2, homogeneous=False)
        self.alignment.add(self.table)

        if mime_type in LINK_FORMATS:
            #try:
            link_object = wine.binary.windows_link(filename)
            #except:
            #    print("Couln't load shell link: ", filename)
            #    return

            self.property_label = gtk.Label(_('Link info'))

            prefix = False
            row_nr = 0
            if 'location' in link_object:
                label = gtk.Label(_("Target:"+' '))
                label.set_alignment(0.0, 0.0)
                #try:
                if link_object['location'] == 'network':
                    text = _("A network location")
                else:
                    text = unicode(link_object['location'])
                    try:
                        prefix = wine.prefixes.get_prefixpath_from_filepath(filename)
                        wine.prefixes.use(prefix)
                        text = '{0}\n<small>({1})</small>'.format(
                            text,
                            wine.util.wintounix(text)
                        )
                    except:
                        pass
                label_target = gtk.Label()
                label_target.set_markup(text)
                label_target.set_selectable(True)
                label_target.set_alignment(0.0, 0.0)
                self.table.attach(label, 0,1, row_nr,row_nr+1, gtk.FILL,gtk.FILL, 6,6)
                self.table.attach(label_target, 1,2, row_nr,row_nr+1, gtk.FILL,0, 6,6)
                row_nr += 1
                #except:
                #    pass

            if 'work dir' in link_object:
                label = gtk.Label(_("Execute in:"+' '))
                label.set_alignment(0.0, 0.0)
                try:
                    text = unicode(link_object['work dir'])
                    try:
                        if prefix is False:
                            prefix = wine.prefixes.get_prefixpath_from_filepath(filename)
                            wine.prefixes.use(prefix)
                        text = '{0}\n<small>({1})</small>'.format(
                            text,
                            wine.util.wintounix(text)
                        )
                    except:
                        pass
                    label_dir = gtk.Label()
                    label_dir.set_markup(text)
                    label_dir.set_selectable(True)
                    label_dir.set_alignment(0.0, 0.0)
                    self.table.attach(label, 0,1, row_nr,row_nr+1, gtk.FILL,gtk.FILL, 6,6)
                    self.table.attach(label_dir, 1,2, row_nr,row_nr+1, gtk.FILL,0, 6,6)
                    row_nr += 1
                except:
                    pass

            if 'arguments' in link_object:
                label = gtk.Label(_("Arguments:"+' '))
                label.set_alignment(0.0, 0.5)
                try:
                    label_args = gtk.Label(link_object['arguments'])
                    label_args.set_selectable(True)
                    label_args.set_alignment(0.0, 0.5)
                    self.table.attach(label, 0,1, row_nr,row_nr+1, gtk.FILL,0, 6,6)
                    self.table.attach(label_args, 1,2, row_nr,row_nr+1, gtk.FILL,0, 6,6)
                    row_nr += 1
                except:
                    pass

            if 'show window as' in link_object:
                label = gtk.Label(_("Opens in a:"+' '))
                label.set_alignment(0.0, 0.5)
                try:
                    text = str(link_object['show window as'])
                    if text == 'normal':
                        text = _("Normal window")
                    elif text == 'maximized':
                        text = _("Maximised window")
                    elif text == 'minimized':
                        text = _("Minimised window")
                    label_window = gtk.Label(text)
                    label_window.set_alignment(0.0, 0.5)
                    self.table.attach(label, 0,1, row_nr,row_nr+1, gtk.FILL,0, 6,6)
                    self.table.attach(label_window, 1,2, row_nr,row_nr+1, gtk.FILL,0, 6,6)
                    row_nr += 1
                except:
                    pass

        else:
            self.property_label = gtk.Label(_('Compatibility'))

            self.settings = {}
            self.settings['program'] = os.path.basename(filename.strip())
            # Get Windows version used for program, in the form of something like "win2k"
            self.settings['version'] = wine.version.get(self.settings['program'])
            # Translate that version to something readable, like "Windows 2000"
            self.settings['version'] = wine.version.windowsversions[self.settings['version']][0]
            # Get the size of the programs desktop window, or None if it's not set
            self.settings['desktop'] = wine.desktop.get(self.settings['program'])

            #
            # Setup widgets
            #

            version_label = gtk.Label(_('Operate as:'))
            version_label.set_alignment(0.0, 0.5)
            self.version_value = gtk.combo_box_new_text()
            for version in ['Windows 7', 'Windows Vista', 'Windows 2003', 'Windows XP %s' % _("(default)"), 'Windows 2000', 'Windows NT 4.0', 'Windows NT 3.51', 'Windows ME', 'Windows 98', 'Windows 95', 'Windows 3.11', 'Windows 3.0', 'Windows 2.0']:
                self.version_value.append_text(version)
            self.table.attach(version_label, 0,1, 0,1, gtk.FILL,0, 6,6)
            self.table.attach(self.version_value, 1,2, 0,1, gtk.FILL,0, 6,6)

            desktop_label = gtk.Label(_('Open in:'))
            desktop_label.set_alignment(0.0, 0.0)
            desktop_value_box = gtk.VBox()
            self.desktop_value_check = gtk.CheckButton(_('Open program windows in a virtual desktop'))
            desktop_value_box.pack_start(self.desktop_value_check)
            self.desktop_table = gtk.Table(rows=2, columns=3, homogeneous=False)
            desktop_width = gtk.Label(_('Desktop width: '))
            desktop_width.set_padding(24,0)
            desktop_width.set_alignment(0.0, 0.5)
            self.desktop_width_spin = gtk.SpinButton(climb_rate=1.0)
            self.desktop_width_spin.get_adjustment().set_all(1024.0, lower=0, upper=10000, step_increment=1, page_increment=10, page_size=0)
            desktop_width_label = gtk.Label(_('pixels'))
            desktop_width_label.set_padding(6,0)
            desktop_height = gtk.Label(_('Desktop height: '))
            desktop_height.set_padding(24,0)
            desktop_height.set_alignment(0.0, 0.5)
            self.desktop_height_spin = gtk.SpinButton(climb_rate=1.0)
            self.desktop_height_spin.get_adjustment().set_all(768.0, lower=0, upper=10000, step_increment=1, page_increment=10, page_size=0)
            desktop_height_label = gtk.Label(_('pixels'))
            desktop_height_label.set_padding(6,0)
            self.desktop_table.attach(desktop_width, 0,1, 0,1, gtk.FILL,0, 0,0)
            self.desktop_table.attach(self.desktop_width_spin, 1,2, 0,1, gtk.FILL,0, 0,0)
            self.desktop_table.attach(desktop_width_label, 2,3, 0,1, gtk.FILL,0, 0,0)
            self.desktop_table.attach(desktop_height, 0,1, 1,2, gtk.FILL,0, 0,0)
            self.desktop_table.attach(self.desktop_height_spin, 1,2, 1,2, gtk.FILL,0, 0,0)
            self.desktop_table.attach(desktop_height_label, 2,3, 1,2, gtk.FILL,0, 0,0)
            desktop_value_box.pack_start(self.desktop_table)
            self.table.attach(desktop_label, 0,1, 1,2, gtk.FILL,gtk.FILL, 6,6)
            self.table.attach(desktop_value_box, 1,2, 1,2, gtk.FILL,0, 6,6)

            #
            # Load settings into widgets
            #

            GtkSelectCombobox(self.version_value, self.settings['version'], startswith=True)
            if self.settings['desktop']:
                self.desktop_value_check.set_active(True)
                self.desktop_width_spin.set_value(self.settings['desktop'][0])
                self.desktop_height_spin.set_value(self.settings['desktop'][1])
                self.desktop_table.set_sensitive(True)
            else:
                self.desktop_value_check.set_active(False)
                self.desktop_width_spin.set_value(1024.0)
                self.desktop_height_spin.set_value(768.0)
                self.desktop_table.set_sensitive(False)

            #
            # Connect widget logic
            #

            self.version_value.connect("changed", self.set_version)
            self.desktop_value_check.connect("toggled", self.set_desktop)
            self.desktop_width_spin.connect("value_changed", self.set_desktop_size)
            self.desktop_height_spin.connect("value_changed", self.set_desktop_size)

        self.alignment.show_all()

        return nautilus.PropertyPage("NautilusPython::vineyard",
                                     self.property_label, self.alignment),

    def set_version(self, combobox):
        selected = combobox.get_model()[combobox.get_active()][0]
        # Fix the special case of Windows 7 being called Windows 2008 in Wine
        if selected == 'Windows 7':
            selected = 'Windows 2008'
        # Remove any " (default)" from the name
        selected = selected.split(' (')[0]
        # Convert the name (f.x. Windows 2000) to the version number (f.x. win2k)
        for i in [ (key, value[0]) for key,value in wine.version.windowsversions.iteritems() ]:
            if i[1] == selected:
                self.settings['version'] = i[0]
        wine.version.set(self.settings['version'], self.settings['program'])

    def set_desktop(self, checkbox):
        if checkbox.get_active():
            self.desktop_table.set_sensitive(True)
            self.settings['desktop'] = (
                self.desktop_width_spin.get_value_as_int(),
                self.desktop_height_spin.get_value_as_int()
            )
            wine.desktop.set(True, size=self.settings['desktop'], program=self.settings['program'])
        else:
            self.desktop_table.set_sensitive(False)
            self.settings['desktop'] = None
            wine.desktop.set(False, program=self.settings['program'])

    def set_desktop_size(self, spinbutton):
        self.settings['desktop'] = (
            self.desktop_width_spin.get_value_as_int(),
            self.desktop_height_spin.get_value_as_int()
        )
        wine.desktop.set(True, size=self.settings['desktop'], program=self.settings['program'])

def GtkSelectCombobox(combobox, string, startswith=False):
    string = string.lower()
    model = combobox.get_model()
    for rownr in range(len(model)):
        if (startswith and model[rownr][0].lower().startswith(string)) or (not startswith and model[rownr][0].lower() == string):
            combobox.set_active(rownr)
            break
