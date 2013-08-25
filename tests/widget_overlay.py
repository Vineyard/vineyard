#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard

import gtk, gobject, cairo, pango

def set_loading_overlay(widget, state=True):
    def _expose_event(widget, event):
        # Setup Cairo drawing area
        context = widget.window.cairo_create()
        region = gtk.gdk.region_rectangle(gtk.gdk.Rectangle(0,0, widget.allocation.width, widget.allocation.height))
        region_exposed = gtk.gdk.region_rectangle(event.area)
        region.intersect(region_exposed)
        context.region(region)
        context.clip()
        
        # Fill with window background color at 0.5 opacity
        context.set_source_rgb(*gdk_color_to_float(widget.get_style().bg[gtk.STATE_NORMAL]))
        context.fill_preserve()
        context.paint_with_alpha(0.5)
        
        # Draw loading label
        cairo_add_text_in_widget_style(context, "Loading...", widget, size_factor=1.4, weight='bold', alignment='center')
    
    if state:
        widget.overlayed = True
        widget._overlay_signal_id = widget.connect_after('expose-event', _expose_event)
    elif 'overlayed' in dir(widget):
        widget.overlayed = False
        widget.disconnect(widget._overlay_signal_id)
    widget.window.invalidate_rect(gtk.gdk.Rectangle(0,0, widget.allocation.width, widget.allocation.height), True)
    widget.window.process_updates(True)

def pixbuf_from_widget(widget):
    widget.window.process_updates(True)
    x, y, width, height, bit_depth = widget.window.get_geometry()
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
    pixbuf.get_from_drawable(widget.window,
        widget.window.get_colormap(),
        0, 0, 0, 0, width, height)
    return pixbuf

def cairo_add_text_in_widget_style(context, text, widget=None, size_factor=1.2, weight='normal', alignment='left'):
    weight = {'normal':cairo.FONT_WEIGHT_NORMAL, 'bold':cairo.FONT_WEIGHT_BOLD}[weight.lower()]
    
    if widget != None:
        context.set_source_rgb(*gdk_color_to_float(widget.get_style().text[gtk.STATE_NORMAL]))
        context.select_font_face(widget.get_style().font_desc.get_family(),
            cairo.FONT_SLANT_NORMAL, weight)
        context.set_font_size(pango.PIXELS(widget.get_style().font_desc.get_size())*size_factor)
    
    x_bearing, y_bearing, width, height = context.text_extents(text)[:4]
    
    if alignment.lower() == 'left':
        context.move_to(
            x_bearing,
            widget.allocation.height/2 - height / 2 - y_bearing
        )
    elif alignment.lower() == 'right':
        context.move_to(
            widget.allocation.width - width - x_bearing,
            widget.allocation.height/2 - height / 2 - y_bearing
        )
    elif alignment.lower() == 'center':
        context.move_to(
            widget.allocation.width/2 - width / 2 - x_bearing,
            widget.allocation.height/2 - height / 2 - y_bearing
        )
    
    context.show_text(text)

def gdk_color_to_float(gdk_color):
    return gdk_color.red/65535., gdk_color.green/65535., gdk_color.blue/65535.

#pixbuf = gtk.gdk.Pixbuf( gtk.gdk.COLORSPACE_RGB, False, 8, 640, 480)
#>             pixbuf.get_from_drawable( self.movie_window.window,
#> self.movie_window.get_colormap(), 0, 0, 0, 0, 640, 480)

def toggle(*args):
    set_loading_overlay(b, not b.overlayed)

w = gtk.Window()
v = gtk.VBox(spacing=6)
w.add(v)
b = gtk.Button("Hello World")
v.pack_start(b)
b.overlayed = False
b2 = gtk.Button("Toggle")
b2.connect('clicked', toggle)
v.pack_start(b2)
w.show_all()

#gobject.idle_add(pixbuf_from_widget, b)

#gobject.timeout_add(50, gtk.main_quit)
gtk.main()
