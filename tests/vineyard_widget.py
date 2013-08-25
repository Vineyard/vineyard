#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
from __future__ import print_function

import sys, os

sys.path.insert(0, os.path.normpath(
    os.path.abspath(os.path.dirname(sys.argv[0]))+'/../'
))
import gtk
import vineyard
#import wine

class Main():
    def __init__(self, widget):
        self.window = gtk.Window()
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.widget = vineyard.widgets.themes.Widget()
        self.widget = eval('vineyard.widgets.{0}'.format(widget)).Widget()
        self.window.add(self.widget)
        self.window.show_all()

        self.window.connect(
            'destroy', lambda *args: gtk.main_quit()
        )

        self.widget.configure()
        gtk.main()

if len(sys.argv) > 1:
    if sys.argv[1] in ('--list', '-l'):
        print(
            '\n'.join(sorted([
                i for i
                in dir(vineyard.widgets)
                if 'Widget' in dir(eval('vineyard.widgets.{0}'.format(i)))
            ]))
        )
    elif sys.argv[1] in dir(vineyard.widgets):
        main = Main(sys.argv[1])
    else:
        print("widget \"{0}\" not found.", file=sys.stderr)
else:
    print((
        "Usage: {self} WIDGET\n"+
        "Run {self} with the argument --list or -l to see "+
        "the list of available widgets."
    ).format(
            self = os.path.basename(sys.argv[0])
    ))
