#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#

from __future__ import print_function

import copy, os
import gobject, gtk, widget, wine
from vineyard import common, program_handler, icons
import logging
import pprint

logger = logging.getLogger("Wine Preferences - Programs")
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self)
        self.title = _("Programs")
        self.widget_should_expand = True
        self.settings_key = 'programs'
        self._list_updated = False
        self._build_interface()

    def _build_interface(self):
        self.widgets = {}
        self.vbox = gtk.VBox()
        self.vbox.set_spacing(3)

        self.list = common.list_view_new_icon_and_text(headers=None, ignore_first_column=True, one_header=True, select_multiple=False)
        self.vbox.pack_start(self.list)

        self.widgets['table'] = gtk.Table(rows=2, columns=2)
        self.widgets['table'].set_col_spacings(3)
        self.widgets['table'].set_row_spacings(3)
        self.vbox.pack_start(self.widgets['table'], expand=False, fill=True)

        self.widgets['button_run'] = common.button_new_with_image('gtk-execute', _("_Run"))
        self.widgets['table'].attach(self.widgets['button_run'], 0,1, 0,1,
                                     xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL)

        self.widgets['button_uninstall'] = common.button_new_with_image('gtk-remove', _("_Uninstall"))
        self.widgets['table'].attach(self.widgets['button_uninstall'], 1,2, 0,1,
                                     xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL)

        self.widgets['button_add'] = common.button_new_with_image('gtk-add', _("A_dd unlisted program"))
        self.widgets['table'].attach(self.widgets['button_add'], 0,2, 1,2,
                                     xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL)

        self.widgets['menu_programs'] = gtk.Menu()
        self.widgets['menu_programs_edit'] = gtk.MenuItem(_("_Edit program"), True)
        self.widgets['menu_programs'].append(self.widgets['menu_programs_edit'])
        self.widgets['menu_programs_separator'] = gtk.SeparatorMenuItem()
        self.widgets['menu_programs'].append(self.widgets['menu_programs_separator'])
        self.widgets['menu_programs_refresh'] = gtk.MenuItem(_("_Refresh program list"), True)
        self.widgets['menu_programs'].append(self.widgets['menu_programs_refresh'])
        self.widgets['menu_programs'].show_all()

        self.list.connect('changed', self.list_changed)
        self.list.connect('double-click', self.list_double_clicked)
        self.list.connect('right-click', self.list_right_clicked)
        self.widgets['button_run'].connect('clicked', self.button_run_clicked)
        self.widgets['button_uninstall'].connect('clicked', self.button_uninstall_clicked)
        self.widgets['button_add'].connect('clicked', self.button_add_clicked)

        self.widgets['menu_programs_edit'].connect("activate", self.menu_edit_clicked)
        self.widgets['menu_programs_refresh'].connect("activate", self.menu_refresh_clicked)

        self.list.set_drag_test_start_function(self._test_drag_start)
        self.list.set_drag_creation_function(self._drag_creation)

        self.frame = common.frame_wrap(self.vbox, self.title)
        self.pack_start(self.frame, True, True)

        self.dialog_edit_program = DialogEditProgram()
        self.dialog_edit_program.connect('response', self._on_edit_program_response)

        self.sizable = []

        self.show_all()

    def _test_drag_start(self, active_nr, active_text):
        if active_nr != None:
            program_data = self.get_program_data_from_id(active_text)
            if 'exe' in program_data or 'programcommand' in program_data:
                row_nr = self.list.get_row_nr_by_text(active_text)
                pixbuf = self.list.treeview.get_model()[row_nr][1]
                return (pixbuf, True)
        return False

    def _drag_creation(self, active_nr, active_text):
        program_data = self.get_program_data_from_id(active_text)
        if program_data:
            desktopfile = wine.programs.write_desktop_file(program_data)
            if desktopfile:
                return "file://%s" % desktopfile

    def _create_row_from_program(self, index, program_data):
        return (
            index,
            icons.get_icon_pixbuf_from_program(program_data),
            self._get_markup_from_program_data(program_data)
        )

    def _insert_program_in_section(self, section, index, program_data):
        widget.async.execute_in_mainloop(
            self.list.insert_in_section,
            section,
            self._create_row_from_program(
                index, program_data
                ),
            alphabetically = True
        )

    def _format_program_data_for_list(self, program_data):
        if (
            '_registrykey' in program_data and
            program_data['_registrykey'].lower().startswith('steam app ')
            ):
            program_data['name'] = _("{steam_program_name} (Steam)").format(
                steam_program_name = program_data['name']
            )
        return program_data

    def load_settings(self):
        programs = wine.programs.get(from_registry=True, from_menus=True)

        header_programs = _('Programs')
        header_programs_reg = _('Programs from Registry')
        header_menus = _('Programs from menu')
        header_libraries = _('Libraries from Registry')
        header_websites = _('Websites')

        added_headers = dict((
            (header, {
                'added':False, 'index':index
                }) for index, header in enumerate([
                    header_programs, header_programs_reg, header_menus,
                    header_libraries, header_websites
                ])
        ))

        widget.async.execute_in_mainloop(self.list.clear)

        new_program_list = {}
        for index, program in enumerate(programs):
            if program['parsed from'] == 'setting':
                section = header_programs
            elif program['parsed from'] == 'registry':
                if 'programexe' in program or 'programcommand' in program:
                    section = header_programs_reg
                else:
                    section = header_libraries
            elif program['parsed from'] == 'menu':
                if 'is_url' in program:
                    section = header_websites
                else:
                    section = header_menus

            if not added_headers[section]['added']:
                widget.async.execute_in_mainloop(
                    self.list.append_header,
                    section,
                    added_headers[section]['index']
                )
                added_headers[section]['added'] = True

            program = self._format_program_data_for_list(program)

            self._insert_program_in_section(
                section,
                index,
                program
            )
            new_program_list[index] = program

        self.settings[self.settings_key] = {'new_list': new_program_list, 'original_list': copy.copy(new_program_list)}
        self._list_updated = True

    def fill_widgets(self, *args):
        if self._list_updated:
            self._list_updated = False
            self.list.set_sensitive(True)
            self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))
            return

        self.list.clear()

        self.list.set_sensitive(False)
        programs, menus = self.settings[self.settings_key]['original_list']

        registered_programs = dict(
            (unicode(k), v) for (k, v) in programs.iteritems()
            if 'programexe' in v or 'programcommand' in v
        )
        registered_libraries = dict(
            (unicode(k), v) for (k, v) in programs.iteritems()
            if 'programexe' not in v and 'programcommand' not in v
        )

        weblinks = {}
        menu_programs = {}
        for key,value in menus.iteritems():
            if 'is_url' in value:
                weblinks[unicode(key)] = value
            else:
                menu_programs[unicode(key)] = value

        if len(registered_programs):
            self._model_add_section(self.list, _('Registered Programs'), registered_programs, first=True)
        if len(menu_programs):
            self._model_add_section(self.list, _('Menu Programs'), menu_programs)
        if len(registered_libraries):
            self._model_add_section(self.list, _('Registered Libraries'), registered_libraries)
        if len(weblinks):
            self._model_add_section(self.list, _('Websites'), weblinks)

        self.list.set_sensitive(True)

        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))

    def refresh(self, *args):
        self.list.set_sensitive(False)
        self.threading.run_in_thread(self.load_settings, callback = self.fill_widgets)

    def _model_add_section(self, model, header, program_dict, first=False):
        if first == True:
            model.append([None, None, '<header first>%s</header>' % header])
        else:
            model.append([None, None, '<header>%s</header>' % header])
        #for program_id in sorted(program_dict.keys(), key=unicode.lower):
        for program_index in sorted(program_dict, key=lambda i: program_dict[i]['name'].lower()):
            program_data = program_dict[program_index]

            model.append((
                program_index,
                icons.get_icon_pixbuf_from_program(program_data),
                self._get_markup_from_program_data(program_data)
            ))

    def _get_markup_from_program_data(self, program_data):
        if 'description' in program_data:
            return "%s\n<small>%s</small>" % (program_data['name'], program_data['description'])
        else:
            return program_data['name']

    def _gui_set_program_selected(self, active_nr, active_text):
        if active_nr == None:
            self.widgets['button_run'].set_sensitive(False)
            self.widgets['button_uninstall'].set_sensitive(False)
        else:
            program_data = self.get_program_data_from_id(active_text)
            if wine.common.any_in_object(('exe', 'command', 'programcommand'), program_data):
                self.widgets['button_run'].set_sensitive(True)
            else:
                self.widgets['button_run'].set_sensitive(False)
            if 'uninstall' in program_data:
                self.widgets['button_uninstall'].set_sensitive(True)
            else:
                self.widgets['button_uninstall'].set_sensitive(False)
            print("\nSelected program: %s\nData:\n%s" % (active_text, pprint.pformat(program_data)))

    def list_changed(self, listwidget, treeview, active_nr, active_text):
        self._gui_set_program_selected(active_nr, active_text)

    def list_double_clicked(self, listwidget, treeview, active_nr, active_text, event):
        self.button_run_clicked()

    def list_right_clicked(self, listwidget, treeview, active_nr, active_text, event):
        if active_text is not None:
            #program_data = self.get_program_data_from_id(active_text)
            #if 'parsed from' in program_data and program_data['parsed from'] == 'menu':
            #    self.widgets['menu_programs_edit'].hide()
            #else:
            #    self.widgets['menu_programs_edit'].show()
            self.widgets['menu_programs_separator'].show()
            self.widgets['menu_programs_edit'].show()
        else:
            self.widgets['menu_programs_separator'].hide()
            self.widgets['menu_programs_edit'].hide()
        self.widgets['menu_programs'].popup( None, None, None, event.button, event.time)

    def button_run_clicked(self, button=None):
        selected_program = self.get_program_data_from_id(self.list.get_active_text())

        if 'programcommand' in selected_program:
            command = selected_program['programcommand']
        elif 'command' in selected_program:
            command = selected_program['command']
        else:
            command = [selected_program['exe']]

        if (
            # Run in terminal
            selected_program.get('programterminal', False) or
            selected_program.get('type', 'program') == 'terminal'
        ):
            wine.run(
                command,
                name = selected_program['name'],
                use_terminal = True
            )
        else:
            # Run with monitoring
            program_handler.MonitoredProgram(
                command,
                selected_program['name'],
                disable_pulseaudio = selected_program.get('disablepulseaudio', False)
            )

    def button_uninstall_clicked(self, button):
        print(self.list.get_active_text())
        program_data = self.get_program_data_from_id(self.list.get_active_text())
        print("Uninstall: {0}".format(pprint.pformat(program_data)))
        wine.programs.uninstall(
            uninstall = program_data['uninstall']
        )

    def button_add_clicked(self, button):
        selected_program = self.list.get_active_text()
        print("Selected: {0}".format(selected_program))
        self.dialog_edit_program.set(
            id = 'adding',
            name = '',
            command = '',
            comment = '',
            uninstall = '',
            type = 'application',
            icon = None
        )
        self.dialog_edit_program.show_all()

    def menu_edit_clicked(self, button):
        program_id = self.list.get_active_text()
        program_data = self.get_program_data_from_id(program_id)

        icon = icons.get_icon_pixbuf_from_program(
            program_data, self.dialog_edit_program.icon.get_pixel_size()
        )
        command = comment = uninstall = ''
        app_type = 'application'
        # NOTE: These are the default key names for program data in python-wine.
        #       VineyardCommand and so on are only used internally by python-wine.
        if 'programcommand' in program_data:
            command = program_data['programcommand']
        elif 'programexe' in program_data:
            if os.path.exists(program_data['programexe']):
                command = wine.util.unixtowin(program_data['programexe'])
            else:
                command = program_data['programexe']
            command = "'{0}'".format(command)
        if 'description' in program_data:
            comment = program_data['description']
        if 'programterminal' in program_data and program_data['programterminal']:
            app_type = 'terminal'
        if 'uninstall' in program_data:
            uninstall = program_data['uninstall']
        icon = program_data.get(
            'icon',
            program_data.get(
                'programicon',
                program_data.get(
                    'programexe',
                    program_data.get(
                        'exe',
                        None
                    )
                )
            )
        )
        #icon = wine.programs.get_icon(program_data)

        self.dialog_edit_program.set(
            id = program_id,
            name = program_data['name'],
            command = command,
            comment = comment,
            uninstall = uninstall,
            type = app_type,
            icon = icon,
            category = program_data.get('category', 'Wine'),
            showinmenu = program_data.get('showinmenu', True),
            disablepulseaudio = program_data.get('disablepulseaudio', False)
        )
        self.dialog_edit_program.show_all()

    def menu_refresh_clicked(self, button):
        self.refresh()

    def get_program_data_from_id(self, index):
        id = int(index)
        try:
            return self.settings[self.settings_key]['new_list'][index]
        except KeyError:
            debug("Something went wrong, a click was detected on a program I don't know: %s" % index)
            return None

    def _on_edit_program_response(self, dialog, response):
        if response == gtk.RESPONSE_OK:
            new_values = dialog.get()
            if new_values['id'] == 'adding':
                program_data = {}
                program_data['_registrykey'] = 'vineyard-{name}'.format(
                    name = wine.util.string_safe_chars(
                        new_values['name'].lower(),
                        extra_safe_chars = ' ,.-_'
                    )
                )
                program_data['id'] = len(self.settings[self.settings_key]['new_list'])
                program_data['name'] = new_values['name']
                program_data['type'] = new_values['type']
                if new_values['icon'] is not None and len(new_values['icon']):
                    program_data['icon'] = new_values['icon']
                if len(new_values['comment']):
                    program_data['description'] = new_values['comment']
                if len(new_values['command']):
                    program_data['programcommand'] = new_values['command']
                if len(new_values['uninstall']):
                    program_data['uninstall'] = new_values['uninstall']
                if len(new_values['category']):
                    program_data['category'] = new_values['category']
                program_data['showinmenu'] = new_values['showinmenu']
                program_data['disablepulseaudio'] = new_values['disablepulseaudio']
            else:
                program_data = wine.common.copy(
                    self.get_program_data_from_id(new_values['id'])
                )
                program_data['id'] = new_values['id']
                program_data['name'] = new_values['name']
                if len(new_values['comment']) or 'description' in program_data:
                    program_data['description'] = new_values['comment']
                if len(new_values['command']) or 'programcommand' in program_data:
                    program_data['programcommand'] = new_values['command']
                if len(new_values['uninstall']) or 'uninstall' in program_data:
                    program_data['uninstall'] = new_values['uninstall']
                if program_data.get('programterminal', None) != new_values['type']:
                    program_data['programterminal'] = (new_values['type'] == 'terminal')
                if new_values['icon'] != None or 'icon' in program_data:
                    program_data['icon'] = new_values['icon']
                if len(new_values['category']) or 'category' in program_data:
                    program_data['category'] = new_values['category']
                program_data['showinmenu'] = new_values['showinmenu']
                program_data['disablepulseaudio'] = new_values['disablepulseaudio']

            existing_program = self.get_program_data_from_id(program_data['id'])
            if existing_program is not None:
                # Create a copy of the program dict object with the extra default
                # values that the edit dialog will have created, so we can match
                # without matching default values
                existing_program_for_matching = dict(existing_program)
                existing_program_for_matching.setdefault('category', 'Wine;')
                existing_program_for_matching.setdefault('disablepulseaudio', False)
                existing_program_for_matching.setdefault('id', program_data['id'])
                existing_program_for_matching.setdefault('programterminal', False)
                existing_program_for_matching.setdefault('showinmenu', False)
            else:
                existing_program_for_matching = existing_program

            if program_data != existing_program_for_matching:
                if 'programterminal' in program_data:
                    del program_data['programterminal']
                self.settings[self.settings_key]['new_list'][
                    program_data['id']] = program_data

                # New program (add)
                if existing_program is None:
                    self.list.insert_in_section(
                        _('Programs'),
                        self._create_row_from_program(
                            program_data['id'],
                            program_data
                        ),
                        alphabetically = True
                    )
                # Existing program (edit)
                else:
                    row_nr = self.list.get_row_nr_by_text(program_data['id'])
                    self.list.set_cell_value(row_nr, 1,
                                             icons.get_icon_pixbuf_from_program(program_data))
                    self.list.set_cell_value(row_nr, 2,
                                             self._get_markup_from_program_data(program_data))

                self.gobject.emit('settings-changed', self.settings_key, self.set_function, (self.settings[self.settings_key],))

        dialog.hide()


    def set_function(self, settings):
        new_list, original_list = settings['new_list'], settings['original_list']
        for index, program_data in new_list.iteritems():
            if index not in original_list or original_list[index] != program_data:
                if 'type' in program_data:
                    terminal = (program_data['type'] == 'terminal')
                else:
                    terminal = None
                if terminal is not None:
                    program_data['programterminal'] = terminal

                wine.programs.set_program_data(program_data)
                """
                wine.programs.set_program_options(
                    key = program_data['_registrykey'],
                    name = program_data['name'],
                    icon = program_data.get('icon', None),
                    command = program_data.get('programcommand', None),
                    description = program_data.get('description', None),
                    terminal = terminal,
                    uninstall = program_data.get('uninstall', None),
                    menu_file = program_data.get('menu file', None)
                )"""

class DialogEditProgram(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(
            self,
            title = _("Program Information"),
            parent = common.get_main_window(),
            flags = gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
            buttons = (
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OK, gtk.RESPONSE_OK
            )
        )

        self.set_border_width(5)
        self.accel_group = gtk.AccelGroup()
        self.add_accel_group(self.accel_group)

        self.hbox = gtk.HBox()
        self.hbox.set_spacing(6)
        self.vbox.pack_start(
            self.hbox,
            expand = True,
            fill = True,
            padding = 0)

        # Icon setup
        self.vbox_icon = gtk.VBox()
        self.hbox.pack_start(
            self.vbox_icon,
            expand = False,
            fill = False,
            padding = 0)

        self.button_icon = gtk.Button()
        self.button_icon.set_accel_path
        self.button_icon.add_accelerator(
            'grab-focus',
            self.accel_group, ord('i'),
            gtk.gdk.MOD1_MASK,
            0)
        self.vbox_icon.pack_start(
            self.button_icon,
            expand = False,
            fill = False,
            padding = 0)

        self.button_icon_aspectframe = gtk.AspectFrame()
        self.button_icon_aspectframe.set_shadow_type(gtk.SHADOW_NONE)
        self.button_icon.add(self.button_icon_aspectframe)

        self.icon = gtk.Image()
        self.icon.filename = None
        self.button_icon_aspectframe.add(self.icon)

        # Fields setup
        self.table = gtk.Table()
        self.table.set_row_spacings(6)
        self.table.set_col_spacings(6)
        self.hbox.pack_start(
            self.table,
            expand = True,
            fill = True,
            padding = 0)

        row = 0

        self.label_type = gtk.Label(_('_Type:'))
        self.label_type.set_use_underline(True)
        self.label_type.set_alignment(1.0, 0.5)
        self.combobox_type = gtk.combo_box_new_text()
        self.combobox_type.append_text(_('Application'))
        self.combobox_type.append_text(_('Application in Terminal'))
        self.label_type.set_mnemonic_widget(self.combobox_type)
        self.table.attach(self.label_type, 0,1, row,row+1, gtk.FILL, 0)
        self.table.attach(self.combobox_type, 1,3, row,row+1, gtk.EXPAND | gtk.FILL, 0)
        row += 1


        self.label_name = gtk.Label(_('_Name:'))
        self.label_name.set_use_underline(True)
        self.label_name.set_alignment(1.0, 0.5)
        self.entry_name = gtk.Entry()
        self.label_name.set_mnemonic_widget(self.entry_name)
        self.table.attach(self.label_name, 0,1, row,row+1, gtk.FILL, 0)
        self.table.attach(self.entry_name, 1,3, row,row+1, gtk.EXPAND | gtk.FILL, 0)
        row += 1

        self.label_command = gtk.Label(_('Comm_and:'))
        self.label_command.set_use_underline(True)
        self.label_command.set_alignment(1.0, 0.5)
        self.entry_command = gtk.Entry()
        self.label_command.set_mnemonic_widget(self.entry_command)
        self.button_command = gtk.Button(_('_Browse...'))
        self.table.attach(self.label_command, 0,1, row,row+1, gtk.FILL, 0)
        self.table.attach(self.entry_command, 1,2, row,row+1, gtk.EXPAND | gtk.FILL, 0)
        self.table.attach(self.button_command, 2,3, row,row+1, gtk.FILL, 0)
        row += 1

        self.label_comment = gtk.Label(_('Co_mment:'))
        self.label_comment.set_use_underline(True)
        self.label_comment.set_alignment(1.0, 0.5)
        self.entry_comment = gtk.Entry()
        self.label_comment.set_mnemonic_widget(self.entry_comment)
        self.table.attach(self.label_comment, 0,1, row,row+1, gtk.FILL, 0)
        self.table.attach(self.entry_comment, 1,3, row,row+1, gtk.EXPAND | gtk.FILL, 0)
        row += 1

        self.label_uninstall = gtk.Label(_('_Uninstall:'))
        self.label_uninstall.set_use_underline(True)
        self.label_uninstall.set_alignment(1.0, 0.5)
        self.entry_uninstall = gtk.Entry()
        self.label_uninstall.set_mnemonic_widget(self.entry_uninstall)
        self.table.attach(self.label_uninstall, 0,1, row,row+1, gtk.FILL, 0)
        self.table.attach(self.entry_uninstall, 1,3, row,row+1, gtk.EXPAND | gtk.FILL, 0)
        row += 1


        self.label_category = gtk.Label(_('C_ategory:'))
        self.label_category.set_use_underline(True)
        self.label_category.set_alignment(1.0, 0.5)

        self.combobox_category = gtk.ComboBoxEntry()
        self.combobox_category_completion = gtk.EntryCompletion()
        self.combobox_category.child.set_completion(self.combobox_category_completion)
        self.combobox_category_model = gtk.ListStore(str)
        self.combobox_category.set_model(self.combobox_category_model)
        self.combobox_category.set_text_column(0)
        self.combobox_category_completion.set_model(self.combobox_category_model)
        self.combobox_category_completion.set_text_column(0)
        for category in wine.common.XDG_MENU_CATEGORIES:
            self.combobox_category_model.append((category,))

        self.label_category.set_mnemonic_widget(self.combobox_category)

        self.checkbutton_showinmenu = gtk.CheckButton(_('_Show in menu'), True)
        self.checkbutton_showinmenu.set_tooltip_text(
            _("Note that the program may not show up in the menu until you have clicked ok")
        )

        self.table.attach(self.label_category, 0,1, row,row+1, gtk.FILL, 0)
        self.table.attach(self.combobox_category, 1,2, row,row+1, gtk.EXPAND | gtk.FILL, 0)
        self.table.attach(self.checkbutton_showinmenu, 2,3, row,row+1, gtk.EXPAND | gtk.FILL, 0)
        row += 1


        self.label_pulseaudio = gtk.Label(_('_PulseAudio:'))
        self.label_pulseaudio.set_use_underline(True)
        self.label_pulseaudio.set_alignment(1.0, 0.5)

        self.checkbutton_pulseaudio = gtk.CheckButton(_('_Disable PulseAudio whilst running'), True)
        self.checkbutton_pulseaudio.set_tooltip_text(
            _("Shut down PulseAudio when starting this program and start it again afterwards")
        )

        self.label_pulseaudio.set_mnemonic_widget(self.checkbutton_pulseaudio)

        self.table.attach(self.label_pulseaudio, 0,1, row,row+1, gtk.FILL, 0)
        self.table.attach(self.checkbutton_pulseaudio, 1,3, row,row+1, gtk.EXPAND | gtk.FILL, 0)
        row += 1


        self._set_default_icon()

        self.connect('delete-event', self._destroy)
        self.connect('destroy-event', self._destroy)
        self.set_deletable(False)

        self.filechooser_command = FileChooserProgram()
        self.filechooser_icon = FileChooserIcon()
        self.button_command.connect('clicked', self._on_edit_program_command)
        self.button_icon.connect('clicked', self._on_edit_program_icon)

        self.filechooser_command.connect('response', self._on_filechooser_command_response)
        self.filechooser_icon.connect('response', self._on_filechooser_icon_response)

    def _destroy(self, *args):
        return True

    def _set_default_icon(self):
        self.icon.set_pixel_size(48)
        try:
            pixbuf = gtk.icon_theme_get_default().load_icon(
                'application-x-executable', 48, 0
            )
            self.icon.set_from_pixbuf(pixbuf)
        except glib.GError:
            pass
        #self.icon.set_from_icon_name('application-x-executable', 48)

    def set(self, id, name='', command='', comment='', uninstall='', type='application', icon=None, category='Wine', showinmenu=False, disablepulseaudio=False):
        self.id = id
        if id == 'adding':
            self.entry_name.grab_focus()

        self.entry_name.set_text(name)
        self.entry_command.set_text(command)
        self._filechooser_set_folder_from_file(
            self.filechooser_command,
            command
        )
        self.entry_comment.set_text(comment)
        self.entry_uninstall.set_text(uninstall)
        if type.lower() == 'application' or type.lower() == 'app':
            self.combobox_type.set_active(0)
        else:
            self.combobox_type.set_active(1)
        self.combobox_category.child.set_text(category)
        self.checkbutton_showinmenu.set_active(showinmenu)
        self.checkbutton_pulseaudio.set_active(disablepulseaudio)
        self._set_default_icon()
        self.icon.filename = None
        if icon is not None and len(icon):
            self._set_icon(icon)

    def get(self):
        if self.combobox_type.get_active() == 0:
            type = 'application'
        else:
            type = 'terminal'
        return {
            'id': self.id,
            'name': self.entry_name.get_text(),
            'command': self.entry_command.get_text(),
            'comment': self.entry_comment.get_text(),
            'uninstall': self.entry_uninstall.get_text(),
            'type': type,
            'icon': self.icon.filename,
            'category': self.combobox_category.child.get_text(),
            'showinmenu': self.checkbutton_showinmenu.get_active(),
            'disablepulseaudio': self.checkbutton_pulseaudio.get_active()
        }


    def _set_icon(self, icon):
        pixbuf = common.pixbuf_new_from_any_file(
            icon,
            size = self.icon.get_pixel_size()
        )
        if pixbuf:
            self.icon.set_from_pixbuf(pixbuf)
            self.icon.filename = icon
        self._filechooser_set_folder_from_file(
            self.filechooser_icon,
            icon
        )

    def _on_edit_program_command(self, *args):
        self._filechooser_set_folder_from_file(
            self.filechooser_command,
            self.entry_command.get_text()
        )
        self.filechooser_command.show_all()

    def _on_filechooser_command_response(self, filechooser, response):
        if response == gtk.RESPONSE_OK:
            file_name = filechooser.get_filename()
            if file_name is not None:
                file_name = wine.util.unixtowin(file_name)
                self.entry_command.set_text(
                    "'{0}'".format(file_name)
                )
                # Set the icon to be the executable as well, if that's not set
                if self.icon.filename is None:
                    self._set_icon(file_name)
        filechooser.hide()

    def _on_edit_program_icon(self, *args):
        self._filechooser_set_folder_from_file(
            self.filechooser_icon,
            self.icon.filename
        )
        self.filechooser_icon.show_all()

    def _on_filechooser_icon_response(self, filechooser, response):
        if response == gtk.RESPONSE_OK:
            file_name = filechooser.get_preview_filename()
            self._set_icon(file_name)
        filechooser.hide()

    def _filechooser_set_folder_from_file(self, filechooser, filename):
        dirname = None
        basename = None
        if filename is not None and len(filename):
            """ If this is a UNIX path """
            if filename[0] == '/':
                dirname = os.path.dirname(filename)
            else:
                if filename[1:3] != ':\\':
                    filename = wine.util.string_split(filename)[0]
                dirname = os.path.dirname(wine.util.wintounix(filename))
                basename = os.path.basename(wine.util.wintounix(filename))
            if not os.path.isdir(dirname):
                dirname = None
                basename = None
        if dirname is None:
            """ Set the directory to the first drive of the configuration """
            dirname = wine.drives.get_main_drive()['mapping']

        if basename is None:
            filechooser.set_current_folder(dirname)
        else:
            if os.path.exists(wine.util.wintounix(filename)):
                filechooser.select_filename(wine.util.wintounix(filename))


class FileChooserProgram(gtk.FileChooserDialog):
    def __init__(self, command = ''):
        gtk.FileChooserDialog.__init__(
            self,
            parent = common.get_main_window(),
            action = gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons = (
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OK, gtk.RESPONSE_OK
            )
        )
        self.image_previewer = gtk.Image()
        self.set_preview_widget(self.image_previewer)
        self.connect('selection_changed', self._file_preview)
        self.set_deletable(False)

        self.add_filter(common.filefilters['all'])
        self.add_filter(common.filefilters['windows_executables'])
        self.set_filter(common.filefilters['windows_executables'])

        self.connect('delete-event', self._destroy)
        self.connect('destroy-event', self._destroy)
        self.set_deletable(False)

    def _destroy(self, *args):
        return True

    def _file_preview(self, filechooser = None):
        filename = self.get_preview_filename()
        if filename and os.path.isfile(filename):
            pixbuf = common.pixbuf_new_from_any_file(filename)
            if pixbuf == None:
                self.set_preview_widget_active(False)
            else:
                self.image_previewer.set_from_pixbuf(pixbuf)
                self.set_preview_widget_active(True)

class FileChooserIcon(gtk.FileChooserDialog):
    def __init__(self, icon = ''):
        gtk.FileChooserDialog.__init__(
            self,
            parent = common.get_main_window(),
            action = gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons = (
                gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OK, gtk.RESPONSE_OK
            )
        )
        self.image_previewer = gtk.Image()
        self.set_preview_widget(self.image_previewer)
        self.connect('selection_changed', self._file_preview)
        self.set_deletable(False)

        self.add_filter(common.filefilters['all'])
        self.add_filter(common.filefilters['windows_executables_and_images'])
        self.set_filter(common.filefilters['windows_executables_and_images'])

        self.connect('delete-event', self._destroy)
        self.connect('destroy-event', self._destroy)
        self.set_deletable(False)

    def _destroy(self, *args):
        return True

    def _file_preview(self, filechooser = None):
        filename = self.get_preview_filename()
        if filename and os.path.isfile(filename):
            pixbuf = common.pixbuf_new_from_any_file(filename)
            if pixbuf == None:
                self.set_preview_widget_active(False)
            else:
                self.image_previewer.set_from_pixbuf(pixbuf)
                self.set_preview_widget_active(True)