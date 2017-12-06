#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import gtk, glib, widget, wine, os
from vineyard import common, program_handler

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self)
        self.title = _("Run executable")
        self.icon = 'gtk-execute'
        self._build_interface()

    def _build_interface(self):
        self.hbox = gtk.HBox()
        self.label = gtk.Label('%s: ' % self.title)
        self.hbox.pack_start(self.label, False, False)
        self.filechooser = gtk.FileChooserButton(_("Select an executable"))
        self.filechooser.add_filter(common.filefilters['all'])
        self.filechooser.add_filter(common.filefilters['windows_executables'])
        self.filechooser.set_filter(common.filefilters['windows_executables'])
        self.filechooser.connect('file-set', self._on_filechooser_file_set)
        try:
            main_drive = wine.drives.get_main_drive(use_registry=False)['mapping']
            self.filechooser.add_shortcut_folder(main_drive)
        except:
            pass
        self.hbox.pack_start(self.filechooser, True, True)
        self.button_run = common.button_new_with_image(self.icon, label=_("_Run"), use_underline=True)
        self.hbox.pack_end(self.button_run, False, False)
        self.pack_start(self.hbox, True, False)
        self.button_run.set_sensitive(False)
        self.show_all()

        self.button_run.connect('clicked', self.button_clicked)

    def on_reset(self):
        try:
            folders = [ i for i in self.filechooser.list_shortcut_folders() ]
        except TypeError:
            folders = []
        for folder in self.filechooser.list_shortcut_folders():
            self.filechooser.remove_shortcut_folder(folder)
        try:
            main_drive = wine.drives.get_main_drive(use_registry=False)['mapping']
            self.filechooser.add_shortcut_folder(main_drive)
        except glib.GError:
            pass

    def button_clicked(self, button):
        if self.gobject.loading: return False

        filename = self.filechooser.get_filename()
        if filename != None:
            program_handler.MonitoredProgram([filename], os.path.basename(filename))

    def _on_filechooser_file_set(self, filechooser):
        file_name = filechooser.get_filename()
        if file_name is not None:
            self.button_run.set_sensitive(True)
        else:
            self.button_run.set_sensitive(False)

