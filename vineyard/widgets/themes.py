#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
from __future__ import print_function

import copy
import gtk, widget, wine
from vineyard import common
from vineyard import gtkwidgets

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self)
        self.title = "Themes"
        self.widget_should_expand = True
        self.settings_key = 'themes'
        self._build_interface()

    def _build_interface(self):
        self.list =  gtkwidgets.simplelist.SimpleList(
            headers = ["Theme", "Active"],
            types = [int, str, bool],
            selection_type = 'multiple'
        )
        #self.list = common.list_view_new_text(select_multiple=False)
        self.pack_start(self.list)
        self.hbox = gtk.HBox()
        self.hbox.set_spacing(6)
        self.pack_start(self.hbox, False, False)
        self.button_add = gtk.Button(stock=gtk.STOCK_ADD)
        #self.button_add.set_sensitive(False)
        self.hbox.pack_start(self.button_add)
        self.button_remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.button_remove.set_sensitive(False)
        self.hbox.pack_start(self.button_remove)


        self.filechooserdialog = common.filechooserdialog_new_with_filters(
            title = _('Select a theme archive'),
            parent = common.widget_get_top_parent(self),
            filters = [
                 common.filefilters['all']
                ,common.filefilters['msstyles']
#                ,common.filefilters['archives']
            ],
            default_filter = 'msstyles',
            action = gtk.FILE_CHOOSER_ACTION_OPEN,
            on_response_func = self._dialog_response
        )

        self.list.connect('changed', self.list_changed)
        self.list.connect('toggled', self.theme_toggled)
        self.button_add.connect('clicked', self.button_add_clicked)
        self.button_remove.connect('clicked', self.button_remove_clicked)

        self.show_all()

    def list_changed(self, listwidget, treeview, active_nr, active_text):
        self.button_remove.set_sensitive(active_nr != None)
    
    def theme_toggled(self, listwidget, row_nr, col_nr, toggled_value):
        toggled_theme = self.themes[ listwidget.model[row_nr][1] ]
        self.settings[self.settings_key]['new_theme'] = toggled_theme['name']
        self.gobject.emit('settings-changed', self.settings_key, self.set_function, (self.settings[self.settings_key],))

    def button_remove_clicked(self, button):
        themes_to_remove = self.list.get_active_text()
        self.list.remove_by_text(themes_to_remove)
        try:
            for theme in themes_to_remove:
                self.gobject.emit('settings-changed',
                                  'themes_remove',
                                  self.remove_theme,
                                  (theme,)
                )
        except ValueError:
            print("Can't remove non-existing theme. How did this happen?")

    def remove_theme(self, theme):
        print("Removing",theme)
        try:
            wine.appearance.remove_theme(theme)
        except:
            pass

    def button_add_clicked(self, button):
        self.filechooserdialog.show_all()

    def _dialog_response(self, dialog, response):
        if response == gtk.RESPONSE_OK:
            file_name = dialog.get_filename()
            print(file_name)
            mimetype = wine.util.file_get_mimetype(file_name)
            if mimetype in wine.util.SUPPORTED_ARCHIVE_MIMETYPES:
                print("Extract and use msstyle - do more (backgrounds, fonts, ...)?")
                file_names = wine.util.archive_list_files(file_name)
                print(file_names)
                file_names_msstyle = [
                    i for i in file_names
                    if i.lower().endswith('.msstyles')
                ]
                if len(file_names_msstyle):
                    print("Found msstyle: {0}".format(
                        wine.common.list_to_english_and(file_names_msstyle)
                    ))
            elif mimetype in common.mimetypes['msstyles']:
                print("MSStyles:")
                #print(wine.binary.windows_executable(file_name).get_version_fast())
                try:
                    wine.appearance.install_theme(file_name)
                    self.set_function()
                    self.fill_widgets()
                except Exception, error:
                    print("Installation of theme failed with error:", error)
        dialog.hide()
        """new_theme = self.comboboxentry.child.get_text()
        self.settings[self.settings_key]['new_list'].append(new_theme)
        self.settings[self.settings_key]['new_list'].sort()
        self.list.set_from_list(self.settings[self.settings_key]['new_list'])
        self.button_add.set_sensitive(False)
        self.gobject.emit('settings-changed', self.settings_key, self.set_function, (self.settings[self.settings_key],))"""

    def set_function(self, settings):
        new_theme, original_theme = settings['new_theme'], settings['original_theme']
        if new_theme != original_theme:
            wine.appearance.set_theme(new_theme)

    def load_settings(self):
        theme = wine.appearance.get_theme()
        self.themes = wine.appearance.list_themes()
        self.settings[self.settings_key] = {'new_theme': theme, 'original_theme': copy.copy(theme)}

    def fill_widgets(self):
        self.list.clear()
        #for index, theme in enumerate(self.themes.keys()+['Hello']):
        for index, theme in enumerate(self.themes.keys()):
            self.list.add([index, theme, False])

        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))
