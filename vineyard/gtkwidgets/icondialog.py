#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#

import gobject, gtk
import vineyard

class IconDialog(gtk.Dialog):
    def __init__(self, *args, **kwargs):
        dialog_kwargs = kwargs.copy()
        for arg in ('image', 'pixbuf', 'text', 'text_secondary'):
            try:
                del dialog_kwargs[arg]
            except:
                pass
        gtk.Dialog.__init__(self, *args, **dialog_kwargs)

        self.set_icon_name('vineyard')

        self.hbox = gtk.HBox()
        self.hbox.set_spacing(6)
        self.hbox.set_border_width(6)

        self.innervbox = gtk.VBox()
        self.innervbox.set_spacing(6)

        self.hbox.pack_end(self.innervbox)

        self.vbox.add(self.hbox)

        self.image = gtk.Image()

        if 'image' in kwargs:
            if kwargs['image'][0] == '/':
                pixbuf = vineyard.pixbuf_new_from_any_file(
                    kwargs['image'],
                    size = gtk.icon_size_lookup(gtk.ICON_SIZE_DIALOG)[1]
                )
            else:
                pixbuf = vineyard.pixbuf_new_from_string(
                    kwargs['image'],
                    icon_size = gtk.ICON_SIZE_DIALOG,
                    return_first = True
                )
        elif 'pixbuf' in kwargs:
            pixbuf = kwargs['pixbuf']
        else:
            pixbuf = vineyard.pixbuf_new_from_string(
                'vineyard',
                icon_size = gtk.ICON_SIZE_DIALOG
            )

        self.image.set_from_pixbuf(pixbuf)

        self.image.set_alignment(0.5, 0.0)
        self.hbox.pack_start(self.image, expand=False, fill=False)

        self.label_first = gtk.Label()
        self.label_first.set_alignment(0.0, 0.5)
        self.innervbox.pack_start(self.label_first, expand=False, fill=True)

        if 'text' in kwargs:
            self.set_markup(kwargs['text'])

        self.label_second = gtk.Label()
        self.label_second.set_alignment(0.0, 0.5)
        self.innervbox.pack_start(self.label_second, expand=False, fill=True)

        if 'text_secondary' in kwargs:
            self.set_markup_second(kwargs['text_secondary'])

    def set_markup(self, text):
        self.label_first.set_markup(
            '<big><b>{0}</b></big>'.format(
                text
            )
        )

    def set_markup_second(self, text):
        self.label_second.set_markup(text)