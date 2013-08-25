#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#

import gtk
import vineyard

def on_toggled(simplelist, row, column_nr, content):
    print simplelist, row, column_nr, content

def on_changed(simplelist, row, column_nr, content):
    print simplelist, row, column_nr, content

win = gtk.Window()

simplelist = vineyard.SimpleList(
    headers = ["Pixbuf", "Str", "State", "Combo2", "Active"],
    types = [int, gtk.gdk.Pixbuf, str, list, list, bool],
    combos = [["On", "Off"], ["Yo", "World"]]
)
simplelist.fill([
    [2, 'vineyard-panel-idle', 'Hi!', [0], [0], True],
    [4, 'vineyard', "World!", [1], [1], False]
])
simplelist.connect('toggled', on_toggled)
simplelist.connect('changed', on_toggled)

win.add(simplelist)

win.set_size_request(640, 300)
win.show_all()

win.connect('destroy', lambda *args: gtk.main_quit())

gtk.main()