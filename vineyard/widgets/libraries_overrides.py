#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import copy, operator
import gtk, gobject, glib, widget, wine
from vineyard import common, async
import logging

logger = logging.getLogger("Wine Preferences - Programs")
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self)
        self.title = "Library handling"
        self.widget_should_expand = True
        self.settings_key = 'libraries-overrides'

        self.overrides_info_for_list = [
            ['', _('Disabled'), ],
            ['builtin', _('Only built-in'), ],
            ['native', _('Only native'), ],
            ['builtin,native', _('Built-in, then native'), ],
            ['native,builtin', _('Native, then built-in'), ]
        ]
        self.overrides_info_for_combobox = [
            [
                _("First try built-in Wine library, then native DLL file"),
                'builtin,native'
            ],
            [
                _("First try native DLL file, then built-in Wine library"),
                'native,builtin'
            ],
            [
                _("Only use built-in Wine library"),
                'builtin'
            ],
            [
                _("Only use native Windows DLL file"),
                'native'
            ],
            [
                _("Disable. Don't load this library"),
                ''
            ]
        ]
        self._build_interface()

    def _build_interface(self):
        self.vbox_top = gtk.VBox()
        self.vbox_top.set_spacing(3)
        self.list = common.list_view_new_text(
            headers = [_("DLL"), _("Order")],
            columns = 2,
            select_multiple = True
        )
        self.vbox_top.pack_start(self.list, expand=True, fill=True)
        self.button_remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.button_remove.set_sensitive(False)
        self.vbox_top.pack_start(self.button_remove, expand=False, fill=True)
        self.frame1 = common.frame_wrap(self.vbox_top, _('Existing DLL overrides'))
        self.pack_start(self.frame1, expand=True, fill=True)

        self.vbox_bottom = gtk.VBox()
        self.vbox_bottom.set_spacing(3)

        self.hbox1 = gtk.HBox()
        self.hbox1.set_spacing(6)
        self.comboboxentry = gtk.combo_box_entry_new_text()
        self.comboboxentry.set_wrap_width(5)
        self.hbox1.pack_start(self.comboboxentry, expand=True, fill=True)
        self.button_add = gtk.Button(_('A_dd'))
        self.button_add.set_sensitive(False)
        self.button_add.set_use_underline(True)
        self.hbox1.pack_start(self.button_add, expand=False, fill=True)
        self.vbox_bottom.pack_start(self.hbox1, expand=False, fill=True)

        self.hbox2 = gtk.HBox()
        self.hbox2.set_spacing(6)
        #self.label_override_type = gtk.Label('%s: ' % _('Type'))
        #self.label_override_type.set_alignment(0.0, 0.5)
        #self.hbox2.pack_start(self.label_override_type, expand=True, fill=True)
        self.combobox_type = gtk.combo_box_new_text()
        self.combobox_type.set_sensitive(False)
        for text in [
            _("First try built-in Wine library, then native DLL file"),
            _("First try native DLL file, then built-in Wine library"),
            _("Only use built-in Wine library"),
            _("Only use native Windows DLL file"),
            _("Disable. Don't load this library")
        ]:
            self.combobox_type.append_text(text)
        self.combobox_type.set_active(0)
        self.hbox2.pack_start(self.combobox_type, expand=True, fill=True)
        self.vbox_bottom.pack_start(self.hbox2, expand=False, fill=True)


        self.frame2 = common.frame_wrap(self.vbox_bottom, _('Add new override'))
        self.pack_start(self.frame2, expand=False, fill=False)

        self.list.treeview.add_events(
            gtk.gdk.BUTTON_PRESS_MASK |
            gtk.gdk.KEY_PRESS_MASK
        )
        self.list.connect('changed', self.list_changed)
        self.list.treeview.connect('button-press-event', self.__list_button_pressed)
        self.list.treeview.connect('key-press-event', self.__list_key_pressed)
        self.comboboxentry.connect('changed', self.entry_changed)
        self.button_remove.connect('clicked', self.button_remove_clicked)
        self.button_add.connect('clicked', self.button_add_clicked)

        self.show_all()

    def list_changed(self, listwidget, treeview, active_nr, active_text):
        self.button_remove.set_sensitive(active_nr != None)

    def __list_button_pressed(self, widget, event):
        event_dict = {
            'type': event.type,
            'button': event.button,
            'x': event.x,
            'y': event.y,
            'x_root': event.x_root,
            'y_root': event.y_root
        }
        gobject.idle_add(
            self.list_button_pressed,
            widget,
            event_dict,
            priority = glib.PRIORITY_HIGH
        )
        return False
    def list_button_pressed(self, widget, event):
        if event['type'] in (gtk.gdk._2BUTTON_PRESS, gtk.gdk._3BUTTON_PRESS):
            return False
        if event['button'] in (1, 3):
            try:
                row = self.list.treeview.get_cursor()[0][0]
            except TypeError:
                return False
            column = self.list.treeview.get_path_at_pos(
                int(event['x']), int(event['y'])
            )[1]
            if column is self.list.columns[1]:
                self.list_rotate_order(row, back=(event['button'] == 3))
        return False

    def __list_key_pressed(self,  widget, event):
        event_dict = {
            'time': event.time,
            'keyval': event.keyval,
            'state': event.state,
            'string': event.string
        }
        gobject.idle_add(
            self.list_key_pressed,
            widget,
            event_dict,
            priority=glib.PRIORITY_HIGH
        )
        return False
    def list_key_pressed(self, widget, event):
        row = self.list.treeview.get_cursor()[0][0]
        if event['keyval'] == 65361: # left
            self.list_rotate_order(row, back=True)
        elif event['keyval'] == 65363: # right
            self.list_rotate_order(row, back=False)
        return False

    def list_rotate_order(self, index, back=False):
        current_value = self.list.model[index][1]
        for _index, (internal_value, list_text) in enumerate(self.overrides_info_for_list):
            if current_value == list_text:
                if back:
                    new_index = _index-1
                    if new_index < 0:
                        new_index = len(self.overrides_info_for_list)-1
                else:
                    new_index = _index+1
                    if new_index >= len(self.overrides_info_for_list):
                        new_index = 0

                new_internal_value, new_value = self.overrides_info_for_list[new_index]

                self.list.model[index][1] = new_value
                self.settings[self.settings_key]['new_list'][index] = (
                    self.settings[self.settings_key]['new_list'][index][0],
                    new_internal_value
                )
                self.gobject.emit('settings-changed', self.settings_key, self.set_function, (self.settings[self.settings_key],))
                return

    def entry_changed(self, comboboxentry):
        text = comboboxentry.child.get_text()
        sensitive = (len(text) > 0)
        self.button_add.set_sensitive( sensitive )
        self.combobox_type.set_sensitive( sensitive )

    def button_remove_clicked(self, button):
        libraries_to_remove = self.list.get_active_text()
        self.list.remove_by_text(libraries_to_remove)
        self.settings[self.settings_key]['new_list'] = [
            item for item
            in self.settings[self.settings_key]['new_list']
            if item[0] not in libraries_to_remove
        ]
        self.gobject.emit('settings-changed', self.settings_key, self.set_function, (self.settings[self.settings_key],))

    def _get_index_of_library(self, library):
        library = library.lower()
        for index, (_library, override) in (
            enumerate(self.settings[self.settings_key]['new_list'])
        ):
            if _library.lower() == library:
                return index
        return None

    def _remove_libraries(self, libraries):
        if type(libraries) in (str, unicode):
            libraries = [libraries]
        libraries_to_remove = [ i.lower() for i in libraries ]
        for index, (library, override) in (
            enumerate(self.settings[self.settings_key]['new_list'])
        ):
            if library.lower() in libraries_to_remove:
                self.settings[self.settings_key]['new_list'].pop(index)
                libraries_to_remove.remove(library.lower())
        if libraries_to_remove == []:
            return True
        else:
            return False

    def button_add_clicked(self, button):
        new_library = self.comboboxentry.child.get_text().lower()
        new_override = self.combobox_type.get_active_text()
        new_override = self._format_override_for_internal_use(new_override)

        if new_library.lower().endswith('.dll'):
            new_library = new_library[:-4]

        # If this library is already in our list, replace it
        if self._get_index_of_library(new_library) is not None:
            self._remove_libraries(new_library)

        self.settings[self.settings_key]['new_list'].append((
            new_library,
            new_override
        ))
        self.settings[self.settings_key]['new_list'].sort()
        self.list.set_from_list(self._get_display_list_from_library_list(
            self.settings[self.settings_key]['new_list']
        ))

        self.button_add.set_sensitive(False)
        self.combobox_type.set_sensitive(False)
        self.gobject.emit('settings-changed', self.settings_key, self.set_function, (self.settings[self.settings_key],))

    def set_function(self, settings):
        new_list, original_list = settings['new_list'], settings['original_list']
        simple_new_list = [ i[0] for i in new_list ]
        simple_original_list = [ i[0] for i in original_list ]
        # Remove
        for library in simple_original_list:
            if library not in simple_new_list:
                wine.libraries.set_override(library, None)
        # Add
        for library, state in new_list:
            if library not in simple_original_list:
                wine.libraries.set_override(library, state)

    def load_settings(self):
        libraries = sorted(wine.libraries.get_overrides())
        # libraries is a list of tuples
        # in the form of ('library name', 'override type')
        self.settings[self.settings_key] = {'new_list': libraries, 'original_list': copy.copy(libraries)}
        self.complete_list_of_libraries = wine.libraries.list()

    def fill_widgets(self):
        self.list.set_from_list(self._get_display_list_from_library_list(
            self.settings[self.settings_key]['original_list']
        ))

        for library in self.complete_list_of_libraries:
            self.comboboxentry.append_text(library)

        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))

    def _get_display_list_from_library_list(self, list):
        new_list = []
        for library, override in sorted(list, key=operator.itemgetter(0)):
            new_list.append((
                library,
                self._format_override_for_display_in_list(override)
            ))
        return new_list

    def _format_override_for_display_in_list(self, override):
        for internal_name, display_text in self.overrides_info_for_list:
            if override == internal_name:
                return display_text

    def _format_override_for_internal_use(self, override):
        for display_text, internal_name in self.overrides_info_for_combobox:
            if override == display_text:
                return internal_name
        for internal_name, display_text in self.overrides_info_for_list:
            if override == display_text:
                return internal_name
