#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import widget, wine, os

class Widget(widget.VineyardWidgetEntry):
    def __init__(self):
        widget.VineyardWidgetEntry.__init__(self,
            title = '%s:' % _('Name'),
            settings_key = 'configuration-name',
            get_function = self.get_name,
            set_function = wine.prefixes.set_name,
            hidden_on_load = True)

    def get_name(self):
        prefix = wine.common.ENV['WINEPREFIX']
        if os.path.expanduser(prefix) == os.path.expanduser('~/.wine'):
            name = None
        else:
            name = wine.common.ENV['WINEPREFIXNAME']

        self.settings[self.settings_key] = name
        return name

    def fill_widgets(self):
        if self.settings[self.settings_key] is None:
            self.hide()
        else:
            self.entry.set_text(self.settings[self.settings_key])
            self.show()
        self.gobject.emit('settings-loaded', self.settings_key, (self.settings[self.settings_key],))
