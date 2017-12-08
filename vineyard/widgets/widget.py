#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import gobject, gtk, wine
from vineyard import async
import fnmatch

class VineyardWidget(gtk.VBox):
    def __init__(self, settings = {}, number_of_settings=1, hidden_on_load=False):
        self.title = None
        self.gobject = gobject.GObject()
        if gobject.signal_lookup('settings-changed', self.gobject) == 0:
            gobject.signal_new(
                "settings-changed",
                gobject.GObject,
                gobject.SIGNAL_ACTION,
                gobject.TYPE_NONE,
                (str, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))
        if gobject.signal_lookup('loading-settings', self.gobject) == 0:
            gobject.signal_new(
                "loading-settings",
                gobject.GObject,
                gobject.SIGNAL_ACTION,
                gobject.TYPE_NONE,
                (int,))
        if gobject.signal_lookup('settings-changed', self.gobject) == 0:
            gobject.signal_new(
                "settings-changed",
                gobject.GObject,
                gobject.SIGNAL_ACTION,
                gobject.TYPE_NONE,
                (str, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT))
        if gobject.signal_lookup('settings-loaded', self.gobject) == 0:
            gobject.signal_new(
                "settings-loaded",
                gobject.GObject,
                gobject.SIGNAL_ACTION,
                gobject.TYPE_NONE,
                (str, gobject.TYPE_PYOBJECT))
        self.gobject.loading = True
        self.gobject._loaded = False
        self._gui_initialized = False
        self.gobject.number_of_settings = number_of_settings
        if 'hidden_on_load' not in dir(self):
            self.hidden_on_load = hidden_on_load
        self.threading = async.ThreadedClass()
        self.settings = settings
        gtk.VBox.__init__(self)
        self.set_spacing(0)
        if '_build_interface' in dir(self):
            self._build_interface_real = self._build_interface
            self._build_interface = self._build_interface_wrapper
        else:
            self._gui_initialized = True

    def _build_interface_wrapper(self):
        self._build_interface_real()
        self._gui_initialized = True

    def __configure__(self, *args):
        if not self.gobject._loaded:
            self.gobject._loaded = True
            if 'configure' in dir(self):
                self.configure()
        return False

    def configure(self):
        """ Overload this method to do custom on-show configuration """
        self.threading.run_in_thread(self._load_settings, callback = self._load_settings_done)

    def reset(self):
        self.gobject.loading = True
        self.gobject._loaded = False
        if getattr(self, 'on_reset', False) is not False:
            self.on_reset()

    def _load_settings(self):
        """
        Run the widgets function for loading its values/settings.
        Also sends the "loading-settings" signal and sets the widget as
        insensitive."""
        async.execute_in_mainloop(
            self.set_sensitive, False
        )
        self.gobject.emit('loading-settings', self.gobject.number_of_settings)
        try:
            if getattr(self, 'load_settings', False) is not False:
                self.load_settings()
        except AttributeError, e:
            print e
        gobject.idle_add(self._fill_widgets)

    def _fill_widgets(self):
        """
        Fill the widget with the loaded values.
        If the widget has not been realised/initialised yet, continue trying
        every 250 milliseconds."""
        if getattr(self, 'fill_widgets', False) is not False:
            if self._gui_initialized:
                self.fill_widgets()
            else:
                gobject.timeout_add(250, self._fill_widgets)
        return False

    def _load_settings_done(self, return_value = None):
        self.gobject.loading = False
        self.set_sensitive(True)
        return False

    def show(self):
        if 'parent_widget' in dir(self):
            self.parent_widget.show()
        return gtk.VBox.show(self)

    """
        Helper functions for single-setting callbacks
    """

    def helper_checkbutton_toggled(self, checkbutton, settings_key, function):
        if self.gobject.loading: return False

        self.settings[settings_key] = checkbutton.get_active()
        self.gobject.emit('settings-changed', settings_key, function, (self.settings[settings_key],))

    def helper_combobox_changed(self, combobox, settings_key, match_values, function):
        if self.gobject.loading: return False

        new_value = combobox.get_model()[combobox.get_active()][0]
        for match_value, value in match_values:
            if fnmatch.fnmatch(new_value, match_value):
                self.settings[settings_key] = value
                self.gobject.emit('settings-changed', settings_key, function, (self.settings[settings_key],))
                break

    def helper_entry_changed(self, entry, settings_key, function):
        if self.gobject.loading: return False

        self.settings[settings_key] = entry.get_text()
        self.gobject.emit('settings-changed', settings_key, function, (self.settings[settings_key],))

    def filechooserbutton_changed(self, filechooser, settings_key, function):
        if self.gobject.loading: return False

        if self.mode == gtk.FILE_CHOOSER_ACTION_OPEN:
            self.settings[settings_key] = self.filechooser.get_filename()
        elif self.mode == gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER:
            self.settings[settings_key] = self.filechooser.get_current_folder()

        self.gobject.emit('settings-changed', settings_key, function, (self.settings[settings_key],))

class VineyardWidgetCheckButton(VineyardWidget):
    def __init__(self, title, settings_key, get_function, set_function, hidden_on_load=False):
        VineyardWidget.__init__(self)
        self.title = title
        self.settings_key = settings_key
        self.get_function = get_function
        self.set_function = set_function
        self.hidden_on_load = hidden_on_load
        self._build_interface()

    def _build_interface(self):
        self.checkbutton = gtk.CheckButton(self.title)
        self.pack_start(self.checkbutton)
        self.show_all()

        self.checkbutton.connect('toggled', self.helper_checkbutton_toggled,
            self.settings_key, self.set_function)

    def load_settings(self):
        self.settings[self.settings_key] = self.get_function()

    def fill_widgets(self):
        self.checkbutton.set_active( self.settings[self.settings_key] == True )
        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))

class VineyardWidgetComboBox(VineyardWidget):
    def __init__(self, title, values, match_values, settings_key, get_function, set_function, hidden_on_load=False):
        VineyardWidget.__init__(self)
        self.title = title
        self.values = values
        self.match_values = match_values
        self.settings_key = settings_key
        self.get_function = get_function
        self.set_function = set_function
        self.hidden_on_load = hidden_on_load
        self._build_interface()

    def _build_interface(self):
        self.table = gtk.Table(rows=2, columns=2, homogeneous=False)

        if self.title != None:
            self.label = gtk.Label(self.title)
            self.label.set_alignment(0.0, 0.5)
            self.table.attach(self.label, 0,1, 0,1, gtk.FILL|gtk.EXPAND,0, 0,0)
        self.combobox = gtk.combo_box_new_text()
        for value in self.values:
            self.combobox.append_text(value)
        self.table.attach(self.combobox, 1,2, 0,1, 0,0, 0,0)

        self.pack_start(self.table)
        self.show_all()

        self.sizable = [self.combobox]

        self.combobox.connect('changed', self.helper_combobox_changed,
            self.settings_key, self.match_values, self.set_function)

    def load_settings(self):
        self.settings[self.settings_key] = self.get_function()

    def fill_widgets(self):
        for match_value, value in self.match_values:
            if self.settings[self.settings_key] == value:
                rownr = 0
                for row in self.combobox.get_model():
                    if fnmatch.fnmatch(row[0], match_value):
                        self.combobox.set_active(rownr)
                        break
                    rownr += 1
                break
        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))

class VineyardWidgetEntry(VineyardWidget):
    def __init__(self, title, settings_key, get_function, set_function, hidden_on_load=False):
        VineyardWidget.__init__(self)
        self.title = title
        self.settings_key = settings_key
        self.get_function = get_function
        self.set_function = set_function
        self.hidden_on_load = hidden_on_load
        self._build_interface()

    def _build_interface(self):
        self.table = gtk.Table(rows=1, columns=2, homogeneous=False)

        self.label = gtk.Label(self.title)
        self.label.set_alignment(0.0, 0.5)
        self.table.attach(self.label, 0,1, 0,1, gtk.FILL|gtk.EXPAND,0, 0,0)

        self.entry = gtk.Entry()
        self.table.attach(self.entry, 1,2, 0,1, 0,0, 0,0)

        self.pack_start(self.table)
        self.show_all()

        self.sizable = [self.entry]

        self.entry.connect('changed', self.helper_entry_changed,
            self.settings_key, self.set_function)

    def load_settings(self):
        self.settings[self.settings_key] = self.get_function()

    def fill_widgets(self):
        self.entry.set_text( self.settings[self.settings_key])
        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))

class VineyardWidgetButton(VineyardWidget):
    def __init__(self, title, icon=None, function=None):
        VineyardWidget.__init__(self)
        self.title = title
        self.icon = icon
        self.function = function
        self._build_interface()

    def _build_interface(self):
        if icon == None:
            self.button = gtk.Button(self.title)
        else:
            use_underline = '_' in title
            self.button = common.button_new_with_image(self.icon, label=self.title, use_underline=use_underline)
        self.pack_start(self.button)
        self.show_all()

        if self.function != None:
            self.button.connect('clicked', self.function)

    def button_clicked(self, button):
        if self.gobject.loading: return False

        self.function()

class VineyardWidgetFileChooserButton(VineyardWidget):
    def __init__(self, title, settings_key, get_function, set_function, hidden_on_load=False, mode=gtk.FILE_CHOOSER_ACTION_OPEN, window_title=None):
        VineyardWidget.__init__(self)
        self.title = title
        self.window_title = window_title
        self.mode = mode
        self.settings_key = settings_key
        self.get_function = get_function
        self.set_function = set_function
        self.hidden_on_load = hidden_on_load
        if window_title == None:
            if mode == gtk.FILE_CHOOSER_ACTION_OPEN:
                self.window_title = _("Select a file")
            elif mode == gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER:
                self.window_title = _("Select a folder")
            elif mode == gtk.FILE_CHOOSER_ACTION_SAVE:
                self.window_title = _("Save as...")
            elif mode == gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER:
                self.window_title = _("Create folder...")
        async.execute_in_mainloop(self._build_interface)

    def _build_interface(self):
        self.table = gtk.Table(rows=1, columns=2, homogeneous=False)
        # wine.drives.get_main_drive(use_registry=False)
        self.label = gtk.Label(self.title)
        self.label.set_alignment(0.0, 0.5)
        self.table.attach(self.label, 0,1, 0,1, gtk.FILL|gtk.EXPAND,0, 0,0)

        self.filechooser = gtk.FileChooserButton(self.window_title)
        self.filechooser.set_action(self.mode)
        self.table.attach(self.filechooser, 1,2, 0,1, 0,0, 0,0)

        self.pack_start(self.table)
        self.show_all()

        self.sizable = [self.filechooser]

        self.filechooser.connect('file-set', self.filechooserbutton_changed,
            self.settings_key, self.set_function)

    def load_settings(self):
        self.settings[self.settings_key] = self.get_function()
        if self.mode == gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER and self.settings[self.settings_key][-1] != '/':
            self.settings[self.settings_key] = '%s/' % self.settings[self.settings_key]

    def fill_widgets(self):
        try:
            main_drive = wine.drives.get_main_drive(use_registry=False)['mapping']
            self.filechooser.add_shortcut_folder(main_drive)
        except:
            pass

        if self.mode == gtk.FILE_CHOOSER_ACTION_OPEN:
            self.filechooser.set_filename(self.settings[self.settings_key])
        elif self.mode == gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER:
            self.filechooser.set_current_folder(self.settings[self.settings_key])

        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))
