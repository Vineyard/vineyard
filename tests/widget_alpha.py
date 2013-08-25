import gtk
import cairo, pangocairo, pango

'''
The expose event handler for the event box.

This function simply draws a transparency onto a widget on the area
for which it receives expose events.  This is intended to give the
event box a "transparent" background.

In order for this to work properly, the widget must have an RGBA
colourmap.  The widget should also be set as app-paintable since it
doesn't make sense for GTK+ to draw a background if we are drawing it
(and because GTK+ might actually replace our transparency with its
default background colour).
'''
def transparent_expose(widget, event):
    cr = widget.window.cairo_create()
    cr.set_operator(cairo.OPERATOR_CLEAR)
    
    # Ugly but we don't have event.region
    region = gtk.gdk.region_rectangle(event.area)
    
    cr.region(region)
    cr.fill()
    
    return False

'''
The expose event handler for the window.

This function performs the actual compositing of the event box onto
the already-existing background of the window at 50% normal opacity.

In this case we do not want app-paintable to be set on the widget
since we want it to draw its own (red) background. Because of this,
however, we must ensure that we use g_signal_register_after so that
this handler is called after the red has been drawn. If it was
called before then GTK would just blindly paint over our work.

Note: if the child window has children, then you need a cairo 1.16
feature to make this work correctly.
'''
def _expose_event(widget, event):
    """
    #get our child (in this case, the event box)
    child = widget.get_child()
    
    #create a cairo context to draw to the window
    cr = widget.window.cairo_create()

    #the source data is the (composited) event box
    cr.set_source_pixmap (child.window,
                          child.allocation.x,
                          child.allocation.y)

    #draw no more than our expose event intersects our child
    region = gtk.gdk.region_rectangle(child.allocation)
    r = gtk.gdk.region_rectangle(event.area)
    region.intersect(r)
    cr.region (region)
    cr.clip()

    #composite, with a 50% opacity
    cr.set_operator(cairo.OPERATOR_OVER)
    cr.paint()
    
    region = gtk.gdk.region_rectangle(child.allocation)
    r = gtk.gdk.region_rectangle(event.area)
    region.intersect(r)
    cr.region (region)
    cr.clip()
    color = widget.get_style().bg[gtk.STATE_NORMAL]
    cr.set_source_rgb(65535./color.red, 65535./color.green, 65535./color.blue)
    cr.fill_preserve()
    cr.paint_with_alpha(0.5)
    """
    
    #width, height = widget.window.get_size()
    #pixbuf = pixbuf_from_widget(widget)
    
    #gc = gtk.gdk.GC(widget.window, clip_x_origin = event.area.x, clip_y_origin = event.area.y,
    #widget.window.draw_pixbuf(widget.get_style().white_gc, pixbuf, 0, 0, 0, 0, width, height)
    
    #xgc = widget.window.new_gc()
    #xgc.set_rgb_fg_color(gtk.gdk.color_parse("red"))
    #widget.window.draw_line(xgc, 0, 0, width, height)
    cr = widget.window.cairo_create()
    width = widget.allocation.width
    region = gtk.gdk.region_rectangle(gtk.gdk.Rectangle(0,0, widget.allocation.width, widget.allocation.height))
    r = gtk.gdk.region_rectangle(event.area)
    region.intersect(r)
    cr.region (region)
    cr.clip()
    cr.set_source_rgb(*gdk_color_to_float(widget.get_style().bg[gtk.STATE_NORMAL]))
    cr.fill_preserve()
    cr.paint_with_alpha(0.5)
    
    """cr.set_source_rgb(*gdk_color_to_float(widget.get_style().text[gtk.STATE_NORMAL]))
    cr.select_font_face(widget.get_style().font_desc.get_family(),
        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(pango.PIXELS(widget.get_style().font_desc.get_size())*1.4)
    x_bearing, y_bearing, width, height = cr.text_extents("Loading")[:4]
    cr.move_to(widget.allocation.width/2 - width / 2 - x_bearing, widget.allocation.height/2 - height / 2 - y_bearing)
    cr.show_text("Loading")"""
    cairo_add_text_in_widget_style(cr, "Loading...", widget, size_factor=1.4, weight='bold', alignment='center')
    """pango_context = pangocairo.CairoContext(cr)
    pango_context.set_source_rgb(*gdk_color_to_float(widget.get_style().fg[gtk.STATE_NORMAL]))
    pango_layout = pango_context.create_layout()
    #pango_layout.set_width(width)
    pango_layout.set_font_description(widget.get_style().font_desc)
    pango_layout.set_markup("Loading")
    pango_layout.set_alignment(pango.ALIGN_CENTER)
    pango_context.show_layout(pango_layout)"""
    
    return False

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

def pixbuf_from_widget(widget):
    widget.window.process_updates(True)
    x, y, width, height, bit_depth = widget.window.get_geometry()
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
    pixbuf.get_from_drawable(widget.window,
        widget.window.get_colormap(),
        0, 0, 0, 0, width, height)
    return pixbuf

# Make the widgets
w = gtk.Window()
b = gtk.Button("A Button")
e = gtk.EventBox()

# Put a red background on the window
#red = gtk.gdk.color_parse("red")
#w.modify_bg(gtk.STATE_NORMAL, red)

# Set the colourmap for the event box.
# Must be done before the event box is realised.
#screen = e.get_screen()
#rgba = screen.get_rgba_colormap()
#e.set_colormap(rgba)

# Set our event box to have a fully-transparent background
# drawn on it. Currently there is no way to simply tell GTK+
# that "transparency" is the background colour for a widget.
#e.set_app_paintable(True)
#e.connect("expose-event", transparent_expose)

# Put them inside one another
w.set_border_width(10)
w.add(e)
e.add(b)

# Realise and show everything
w.show_all()

# Set the event box GdkWindow to be composited.
# Obviously must be performed after event box is realised.
#e.window.set_composited(True)

# Set up the compositing handler.
# Note that we do _after_ so that the normal (red) background is drawn
# by gtk before our compositing occurs.
e.connect_after("expose-event", _expose_event)

gtk.main()
