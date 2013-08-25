#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import operator
import widget, wine

class Widget(widget.VineyardWidgetComboBox):
    def __init__(self):
        # Get a list of the Windows versions sorted by version number, newest first
        _windowsversions = wine.version.windowsversions_sorted.copy()
        windows_versions = [
            _('%s (default)') % v[0] if k.endswith('xp') else v[0]
            for (k,v) in _windowsversions
        ]
        match_values = [
            ('*%s*' % value[0], key)
            for key, value in sorted(
                _windowsversions.iteritems(),
                cmp=lambda x,y: y[1][3]-x[1][3]
            )
        ]
        widget.VineyardWidgetComboBox.__init__(self,
            title = '%s:' % _('Operate as'),
            values = windows_versions,
            match_values = match_values,
            settings_key = 'windows-version',
            get_function = wine.version.get,
            set_function = wine.version.set)
