#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import copy, os, string
import gtk, widget, wine
from vineyard import common

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self)
        self.title = "Emulated drives"
        self.widget_should_expand = True
        self.settings_key = 'drives'
        self.DRIVE_TYPES = common.sorteddict(
            ('', _('Autodetect')),
            ('hd', _('Local hard disk')),
            ('network', _('Network share')),
            ('cdrom', _('CDROM')),
            ('floppy', _('Floppy disk'))
        )
        known_drive_types = self.DRIVE_TYPES.keys()
        for d_type in wine.drives.DRIVE_TYPES:
            if d_type not in known_drive_types:
                self.DRIVE_TYPES[d_type] = _(d_type.capitalize())
        self._build_interface()

    def _build_interface(self):
        self.vbox = gtk.VBox()
        self.vbox.set_spacing(6)

        self.vbox_top = gtk.VBox()
        self.vbox_top.set_spacing(0)
        self.list = common.list_view_new_icon_and_text(headers=['', _('Drive'), _('Mapping')], number_of_text_columns=2, select_multiple=False)
        self.vbox_top.pack_start(self.list, True, True)
        self.hbox_buttons = gtk.HBox()
        self.hbox_buttons.set_spacing(6)
        self.button_add = gtk.Button(stock=gtk.STOCK_ADD)
        self.button_add.set_sensitive(True)
        self.hbox_buttons.pack_start(self.button_add, False, False)
        self.button_remove = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.button_remove.set_sensitive(False)
        self.hbox_buttons.pack_start(self.button_remove, False, False)
        self.button_auto = common.button_new_with_image('gtk-refresh', label=_("Autodetect"), use_underline=False)
        self.hbox_buttons.pack_end(self.button_auto, False, False)
        self.vbox_top.pack_start(self.hbox_buttons, False, False)
        self.vbox.pack_start(self.vbox_top, True, True)

        self.vbox_bottom = gtk.VBox()
        self.vbox_bottom.set_spacing(6)
        self.path_entry = gtk.Entry()
        self.path_button = gtk.Button(_('Browse...'))
        self.path_box = common.new_label_with_widget('%s: ' % _('Path'), [
            self.path_entry, self.path_button
        ])
        self.vbox_bottom.pack_start(self.path_box, False, True)

        #self.expander = gtk.Expander(_('Advanced'))
        #self.vbox_bottom.pack_start(self.expander, False, True)
        self.vbox_expander = gtk.VBox()
        self.vbox_expander.set_spacing(6)
        #self.expander.add(self.vbox_expander)
        self.vbox_bottom.pack_start(self.vbox_expander, False, True)

        self.device_entry = gtk.Entry()
        self.device_button = gtk.Button(_('Browse...'))
        self.device_box = common.new_label_with_widget('%s: ' % _('Device'), [
            self.device_entry, self.device_button
        ])
        self.vbox_expander.pack_start(self.device_box, False, True)

        self.hbox_toggle = gtk.HBox()
        self.device_toggle = gtk.CheckButton(_('Use device file for path'))
        self.hbox_toggle.pack_end(self.device_toggle, False, True)
        self.vbox_expander.pack_start(self.hbox_toggle, False, True)

        self.type = gtk.combo_box_new_text()
        for d_type,d_name in self.DRIVE_TYPES:
            self.type.append_text(d_name)
        self.type_box = common.new_label_with_widget('%s: ' % _('Type'), self.type)
        self.vbox_bottom.pack_start(self.type_box, False, True)
        self.vbox.pack_start(self.vbox_bottom, False, True)

        self.list.connect('changed', self.list_changed)
        self.button_add.connect('clicked', self.button_add_clicked)
        self.button_remove.connect('clicked', self.button_remove_clicked)
        self.button_auto.connect('clicked', self.button_auto_clicked)
        self.path_entry.connect('changed', self.path_changed)
        self.path_button.connect('clicked', self.button_path_clicked)
        self.type.connect('changed', self.type_changed)
        self.device_entry.connect('changed', self.device_changed)
        self.device_button.connect('clicked', self.button_device_clicked)
        self.device_toggle.connect_after('toggled', self.device_toggled)

        self.list.renderers[1].connect('edited', self.drive_letter_edit)
        self.list.renderers[1].set_property('editable', True)

        self.list.renderers[2].connect('edited', self.drive_mapping_edit)
        self.list.renderers[2].set_property('editable', True)

        self.frame = common.frame_wrap(self.vbox, self.title)
        self.pack_start(self.frame, True, True)

        self.sizable = [self.path_box.widget, self.type]

        self.show_all()
        self.hbox_toggle.hide()

        self.filechooserdialog_path = common.filechooserdialog_new_with_filters(
            title = _('Select which folder the drive should be mapped to'),
            parent = common.widget_get_top_parent(self),
            action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            on_response_func = self.path_dialog_response)

        self.filechooserdialog_device = common.filechooserdialog_new_with_filters(
            title = _('Select which device file the drive use'),
            parent = common.widget_get_top_parent(self),
            action = gtk.FILE_CHOOSER_ACTION_OPEN,
            on_response_func = self.device_dialog_response)

    def _gui_set_drive_selected(self, state):
        self.button_remove.set_sensitive(state)
        self.vbox_bottom.set_sensitive(state)

    def list_changed(self, listwidget, treeview, active_nr, active_text):
        self._gui_set_drive_selected(active_nr != None)
        if active_nr != None:
            info = self.settings[self.settings_key]['new_list'][active_text]
            self.path_entry.set_text(info['mapping'])
            self.device_entry.set_text(info.get('device', ''))
            if info['type'] in self.DRIVE_TYPES:
                common.combobox_set_active_by_string(self.type, self.DRIVE_TYPES[info['type']])
            else:
                self.type.set_active(0)
            self.device_toggle_visibility_check(
                info.get('device', ''),
                info['mapping']
            )

    def _get_active_drive_info(self):
        return self.settings[self.settings_key]['new_list'][self.list.get_active_text()]

    def drive_letter_edit(self, cell, path, new_text):
        active_nr = self.list.get_active()
        if new_text[-1].strip() == ':':
            new_text = new_text.strip()[:-1].upper()
        old_text = self.list.get_active_text()
        #print "Old text: %s\nNew text: %s" % (old_text, new_text)
        if len(new_text) == 1 and new_text.upper() not in self.settings[self.settings_key]['new_list']:
            self.settings[self.settings_key]['new_list'][new_text] = self.settings[self.settings_key]['new_list'][old_text]
            del self.settings[self.settings_key]['new_list'][old_text]
            self.list.set_cell_value(active_nr, 1, new_text)
            self.emit_change()
            #print self.settings[self.settings_key]['new_list']

    def drive_mapping_edit(self, cell, path, new_text):
        self.path_entry.set_text(new_text)

    def path_changed(self, entry):
        new_path = entry.get_text()
        active_nr = self.list.get_active()
        active_text = self.list.get_active_text()
        current_path = self.settings[self.settings_key]['new_list'][active_text]['mapping']
        if (
            new_path != current_path and
            self._get_mapping_suitable_for_view(new_path) != self._get_mapping_suitable_for_view(current_path)
        ):
            self.list.set_cell_value(active_nr, 2, self._get_mapping_suitable_for_view(new_path))
            self.settings[self.settings_key]['new_list'][active_text]['mapping'] = new_path
            device = get_device_for_path(new_path)
            if device is not None:
                # device_changed will take care of emitting 'settings-changed'
                self.device_entry.set_text(device)
                self.device_changed(self.device_entry)
            else:
                self.emit_change()

    def type_changed(self, combobox):
        active_text = common.combobox_get_active_value(combobox, 0)
        new_type = self.DRIVE_TYPES.get_key_from_value(active_text)
        drive_info = self._get_active_drive_info()
        if new_type != drive_info['type']:
            drive_info['type'] = new_type
            icon = get_drive_icon(drive_info)
            self.list.set_cell_value(self.list.get_active(), 0, icon)
            self.settings[self.settings_key]['new_list'][self.list.get_active_text()]['type'] = new_type
            self.emit_change()

    def device_toggle_visibility_check(self, device_path, path_path=None):
        image_mount_point = None
        if path_path is not None:
            image_mount_point = wine.util.get_mount_iso_path(device_path)

        self.hbox_toggle.hide()
        # If device is a known type of image, show the image hbox
        if device_path[-3:].lower() in wine.drives.SUPPORTED_IMAGE_FORMATS:
            self.hbox_toggle.show_all()
        # If device is already mounted as an image, show the image hbox and
        # toggle "use device as path" on
        if path_path == wine.util.get_mount_iso_path(device_path):
            self.hbox_toggle.show_all()
            self.device_toggle.set_active(True)
        else:
            self.device_toggle.set_active(False)
        self.device_toggled()

    def device_changed(self, entry):
        new_device = entry.get_text()
        active_nr = self.list.get_active()
        active_text = self.list.get_active_text()
        if 'device' in self.settings[self.settings_key]['new_list'][active_text]:
            current_device = self.settings[self.settings_key]['new_list'][active_text]['device']
        else:
            current_device = None

        if new_device != current_device:

            self.device_toggle_visibility_check(
                new_device,
                self.settings[self.settings_key]['new_list'][active_text]['mapping']
            )

            self.settings[self.settings_key]['new_list'][active_text]['device'] = new_device
            self.emit_change()

    def device_toggled(self, widget=None):
        if self.device_toggle.get_active():
            self.path_entry.set_text(
                wine.util.get_mount_iso_path(self.device_entry.get_text())
            )
            self.path_entry.set_sensitive(False)
        else:
            self.path_entry.set_sensitive(True)

    def button_path_clicked(self, button):
        folder = self.path_entry.get_text()
        if not os.path.isdir(folder):
            folder = os.path.dirname(folder)
        self.filechooserdialog_path.set_current_folder(folder)
        self.filechooserdialog_path.show()

    def path_dialog_response(self, dialog, response):
        if response == gtk.RESPONSE_OK:
            mapping = dialog.get_current_folder()
            self.path_entry.set_text(mapping)
        dialog.hide()

    def button_device_clicked(self, button):
        folder = self.device_entry.get_text()
        if not os.path.isdir(folder):
            folder = os.path.dirname(folder)
        self.filechooserdialog_device.set_current_folder(folder)
        self.filechooserdialog_device.show()

    def device_dialog_response(self, dialog, response):
        if response == gtk.RESPONSE_OK:
            device = dialog.get_filename()
            self.device_entry.set_text(device)
        dialog.hide()

    def entry_changed(self, comboboxentry):
        text = comboboxentry.child.get_text()
        self.button_add.set_sensitive( len(text) > 0 and not common.in_list_caseinsensitive(text, self.settings[self.settings_key]['new_list']) )

    def _get_mapping_suitable_for_view(self, mapping):
        if mapping.startswith(wine.common.ENV['WINEPREFIX']):
            return os.path.relpath(mapping, '%s/dosdevices' % wine.common.ENV['WINEPREFIX'])
        return mapping

    def remove_drive(self, drives_to_remove):
        self.list.remove_by_text(drives_to_remove)
        try:
            for drive in drives_to_remove:
                del self.settings[self.settings_key]['new_list'][drive]
        except ValueError:
            print "Can't remove non-existing drive. How did this happen?"
        self.emit_change()

    def button_remove_clicked(self, button):
        drives_to_remove = self.list.get_active_text()
        self.remove_drive(drives_to_remove)

    def button_add_clicked(self, button):
        new_drive = [
            i for i in string.ascii_uppercase[3:]
            if i not in self.settings[self.settings_key]['new_list'].keys()
        ][0]
        self.settings[self.settings_key]['new_list'][new_drive] = {
            'type': '',
            'mapping': '/'
        }
        self.fill_widgets(emit_loaded = False)
        self.emit_change()

    def button_auto_clicked(self, button):
        drives = wine.drives.get_auto_detect()
        for drive in drives.keys():
            if 'type' not in drives[drive]:
                drives[drive]['type'] = ''
            if 'mapping' not in drives[drive]:
                del drives[drive]
        self.settings[self.settings_key]['new_list'] = drives
        self.emit_change()
        self.fill_widgets(emit_loaded=False)

    def set_function(self, settings):
        new_list, original_list = settings['new_list'], settings['original_list']
        # Remove
        for drive_letter in original_list:
            if drive_letter not in new_list:
                #print("Remove drive", drive_letter)
                wine.drives.remove(drive_letter)
        # Add / Update
        for drive_letter, info in new_list.iteritems():
            if (
                (drive_letter not in original_list) or
                (original_list[drive_letter] != info)
            ):
                args = [drive_letter.lower(), info['mapping']]

                kwargs = {}
                for key, kwkey in (
                    ('label', 'label'),
                    ('serial', 'serial'),
                    ('type', 'drive_type'),
                    ('device', 'device_file')
                ):
                    if key in info and info[key] is not None:
                        if key == 'type' and info[key] == '':
                            continue
                        kwargs[kwkey] = info[key]

                #print("Add/Set drive", args, kwargs)
                wine.drives.add(*args, **kwargs)

    def load_settings(self):
        drives = wine.drives.get()
        for drive in drives:
            if 'type' not in drives[drive]:
                drives[drive]['type'] = ''
        self.settings[self.settings_key] = {'new_list': drives, 'original_list': copy.deepcopy(drives)}

    def fill_widgets(self, emit_loaded=True):
        self.list.clear()
        drives = (
            (key, self.settings[self.settings_key]['new_list'][key])
            for key
            in sorted(self.settings[self.settings_key]['new_list'].keys())
        )
        for drive_letter, info in drives:
            icon = get_drive_icon(info)
            mapping = self._get_mapping_suitable_for_view(info['mapping'])
            self.list.append([ icon, drive_letter[0].upper(), mapping ])

        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))

    def emit_change(self):
        #if self.settings[self.settings_key]['new_list'] != self.settings[self.settings_key]['original_list']:
        #    self.gobject.emit('settings-changed', self.settings_key, self.set_function, (self.settings[self.settings_key],))
        self.gobject.emit('settings-changed', self.settings_key, self.set_function, (self.settings[self.settings_key],))

def get_drive_icon(drive, widget=None):
    if drive['type'] == "hd":
        stock_icon = gtk.STOCK_HARDDISK
    elif drive['type'] == "network":
        stock_icon = gtk.STOCK_NETWORK
    elif drive['type'] == "cdrom":
        stock_icon = gtk.STOCK_CDROM
    elif drive['type'] == "floppy":
        stock_icon = gtk.STOCK_FLOPPY
    elif drive['type'] == "":
        if ( True in [
            drive['mapping'].split('/')[-1].lower().startswith(i)
            for i in ("cdrom", "cdrw", "dvd", "dvdrw")
        ]):
            stock_icon = gtk.STOCK_CDROM
        elif (True in [
            drive['mapping'].split('/')[-1].lower().startswith(i)
            for i in ("floppy", "fd")
        ]):
            stock_icon = gtk.STOCK_FLOPPY
        elif (
            drive['mapping'] == '/'
        ) or (
            drive['mapping'].startswith('/media/')
        ) or (
            drive['mapping'].startswith('/mnt/')
        ) or (
            drive['mapping'] == '%s/drive_c' % wine.common.ENV['WINEPREFIX']
        ):
            stock_icon = gtk.STOCK_HARDDISK
        else:
            stock_icon = gtk.STOCK_DIRECTORY
    if widget == None:
        widget = gtk.HBox()
    return widget.render_icon(stock_icon, gtk.ICON_SIZE_BUTTON)

def get_device_for_path(path):
    matches = [
        i['device'] for i
        in wine.util.get_mounted_drives()
        if i['dir'] == path
    ]
    if len(matches):
        return matches[0]
    else:
        return None