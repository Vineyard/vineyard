#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import os, sys
import glib, gobject, gtk, pango, cairo, re
import string
import logging
import threading

logger = logging.getLogger("Wine Preferences - Widgets")
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical

GTK_VERSION = gtk.gtk_version[0]+gtk.gtk_version[1]/100.+gtk.gtk_version[2]/1000.

MAIN_WINDOW = None

class sorteddict(list):
    def __init__(self, *values):
        if values == None:
            list.__init__(self)
        else:
            list.__init__(self, values)

    def __getitem__(self, key):
        for ikey,value in iter(self):
            if key == ikey:
                return value
        raise KeyError(key)

    def __setitem__(self, key, value):
        return self.append((key, value))

    def get_index(self, index):
        return list.__getitem__(self, index)

    def remove_key(self, key):
        if self.__contains__(key):
            for i in range(len(self)):
                i_key, value = self.get_index(i)
                if i_key == key:
                    del self[i]
                    return
            raise KeyError(key)
        elif type(key) == int:
            del self[key]
        else:
            raise KeyError(key)

    def __contains__(self, key):
        for i_key,i_value in self.iteritems():
            if i_key == key:
                return True
        return False

    def get_key_from_value(self, value):
        for i_key,i_value in self.iteritems():
            if i_value == value:
                return i_key
        return None

    def keys(self):
        return [ key for key,value in self ]

    def values(self):
        return [ value for key,value in self ]

    def iteritems(self):
        return ( (key,value) for key,value in self )

    def iterkeys(self):
        return ( key for key,value in self )

    def itervalues(self):
        return ( value for key,value in self )


def get_shared_files_path(app_name="vineyard"):
    """ Set up the Python Path variable to include the current working dir (if that's where the process is running) and return the path to Vineyard's shared files"""
    SHARED_FILES_PATH = None
    current_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    current_file = os.path.basename(sys.argv[0])
    # If we are running from the development directory
    if os.path.isfile( "%s/data/vineyard-preferences.pod" % current_dir ):
        SHARED_FILES_PATH = "%s/data" % current_dir
    elif os.path.isfile( "%s/../data/vineyard-preferences.pod" % current_dir ):
        SHARED_FILES_PATH = os.path.normpath("%s/../data" % current_dir)
    elif os.path.isfile("{dirname}/{basename}.glade".format(
        dirname = current_dir,
        basename = current_file.split('.')[0]
        )):
        SHARED_FILES_PATH = current_dir

    if not SHARED_FILES_PATH is None:
        path_to_add_to_sys_path = os.path.realpath('%s/../python-wine' % (
            SHARED_FILES_PATH
        ))
        if path_to_add_to_sys_path not in sys.path:
            sys.path.insert(0, path_to_add_to_sys_path)
    else:
        for path in [ os.path.sep.join(i.split(os.path.sep)[:-1])
                      for i in os.environ['PATH'].split(':') ]:
            if os.path.isdir( "%s/share/%s" % (path, app_name) ):
                SHARED_FILES_PATH = "%s/share/%s" % (path, app_name)

    icon_theme_default = gtk.icon_theme_get_default()
    if icon_theme_default != None and (
        '%s/icons' % SHARED_FILES_PATH not in icon_theme_default.get_search_path()
        ):
        icon_theme_default.prepend_search_path('%s/icons' % SHARED_FILES_PATH)

    return SHARED_FILES_PATH

def setup_translation(app_name="vineyard", path="%s/%s" % (sys.path[-1], "locale")):
    import locale, gettext
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        try:
            if 'LANGUAGE' in os.environ:
                locale.setlocale(locale.LC_ALL, '%s.UTF-8' % os.environ['LANGUAGE'])
            elif 'LANG' in os.environ:
                locale.setlocale(locale.LC_ALL, '%s.UTF-8' % os.environ['LANG'])
            else:
                print "Locale not supported, running in English"
        except:
            print "Locale not supported, running in English"

    modules = [gettext]
    if 'glade' in dir(gtk):
        modules.append(gtk.glade)
    for module in modules:
        module.bindtextdomain(app_name, path)
        module.textdomain(app_name)
    gettext.install(app_name, path, unicode=True)
    return gettext.gettext

""" If Gettext isn't defined, do it """
if '_' not in dir():
    SHARED_FILES_PATH = get_shared_files_path()
    _ = setup_translation(path="%s/locale" % SHARED_FILES_PATH)

import wine

mimetypes = {
    'windows_executables': (
        'application/x-ms-dos-executable', 'application/x-dosexec'
        'application/x-msdos-program','application/x-msdownload','application/exe',
        'application/x-exe','application/dos-exe','vms/exe','application/x-winexe',
        'application/msdos-windows','application/x-zip-compressed',
#       'application/x-executable',
        'application/x-msi'),
    'images': tuple(sum([ # sum() joins the sub-lists (e.g. from [[1],[2,3]] to [1,2,3])
        i['mime_types']
        for i
        in gtk.gdk.pixbuf_get_formats()
    ], [])),
    'archives': (
        'application/x-gzip'
        ,'application/x-bzip2'
        ,'application/zip'
        #,'application/x-7z-compressed'
        #,'application/x-rar'
    ),
    'msstyles': (
        'application/octet-stream',
        'application/x-ms-dos-executable',
        'application/x-dosexec'
    ),
    'executable': (
        'application/x-executable',
    )
}

filefilters = {
    'all': gtk.FileFilter(),
    'images': gtk.FileFilter(),
    'windows_executables': gtk.FileFilter(),
    'windows_executables_and_images': gtk.FileFilter(),
    'archives': gtk.FileFilter(),
    'msstyles': gtk.FileFilter(),
    'wine_binary': gtk.FileFilter()
}
filefilters['all'].set_name(_("All Files"))
filefilters['images'].set_name(_("Image Files"))
filefilters['windows_executables'].set_name(_("Windows Executables"))
filefilters['windows_executables_and_images'].set_name(_("Windows Executables And Image Files"))
filefilters['archives'].set_name(_("Archives"))
filefilters['msstyles'].set_name(_("Microsoft XP Style"))
filefilters['wine_binary'].set_name(_("Wine Binaries"))


filefilters['all'].add_pattern('*')

filefilters['images'].add_pixbuf_formats()
filefilters['windows_executables_and_images'].add_pixbuf_formats()

# for mimetype in mimetypes['executable']:
#     filefilters['wine_binary'].add_mime_type(mimetype)
# filefilters['wine_binary'].add_pattern('*wine*')
filefilters['wine_binary'].add_custom(
    gtk.FILE_FILTER_DISPLAY_NAME| gtk.FILE_FILTER_MIME_TYPE,
    lambda filter_info, data: (
        'wine' in filter_info[2].lower() and
        filter_info[3] in mimetypes['executable']
    ),
    None
)

filefilters['msstyles'].add_custom(
    gtk.FILE_FILTER_DISPLAY_NAME | gtk.FILE_FILTER_MIME_TYPE,
    lambda filter_info, data: (
        filter_info[3] in mimetypes['msstyles'] and  # MIME_TYPE
        filter_info[2].lower().endswith('.msstyles') # DISPLAY_NAME
    ),
    None
)

for key, mtypes in mimetypes.iteritems():
    if key == 'msstyles': continue
    for mimetype in mtypes:
        if key in filefilters:
            filefilters[key].add_mime_type(mimetype)

for mimetype in mimetypes['images']:
    filefilters['windows_executables_and_images'].add_mime_type(mimetype)

for mimetype in mimetypes['windows_executables']:
    filefilters['windows_executables_and_images'].add_mime_type(mimetype)

for mimetype in mimetypes['archives']:
    filefilters['archives'].add_mime_type(mimetype)


window = gtk.Window()
treeview = gtk.TreeView()
styles = {
    'window': window.get_style(),
    'treeview': treeview.get_style()
}

window.destroy()
treeview.destroy()


class LoadWidgets:
    def __init__(self, handlerclass=None, filename="%s.glade" % os.path.basename(sys.argv[0]).split('.')[0], app_name="vineyard", connect_signals=True):
        xmlfile = None
        if os.path.isfile(filename):
            xmlfile = filename
            #print("Filename used directly")
        else:
            if handlerclass != None and 'path_shared_files' in dir(handlerclass):
                xmlfile = '%s/%s' % (handlerclass.path_shared_files, filename)
                #print("Filename taken from path_share_files")
            elif not filename.startswith('/'):
                xmlfile = '%s/%s' % (os.path.dirname(sys.argv[0]), filename)
                #print("Filename taken from sys.argv[0]")

        if xmlfile == None:
            critical("GtkBuilder XML file not found, exiting.")
            return None

        self._builder = gtk.Builder()
        self._builder.set_translation_domain(app_name)
        # Remove unsupported widgets, somewhat of a hack,
        # but at least we get to support several versions of Gtk.
        file_loaded = False
        if hasattr(gtk, 'Spinner'):
            try:
                self._builder.add_from_file(xmlfile)
                file_loaded = True
            except glib.GError:
                file_loaded = False
        # The above should not fail, but if it does, fallback to not using a
        # GtkSpinner
        if not file_loaded:
            with open(xmlfile, 'r') as f:
                guidata = self._downgrade_xml(f.read())
            self._builder.add_from_string(guidata)

        if connect_signals and handlerclass != None:
            self._builder.connect_signals(handlerclass)
        self._widgets = {}

        # A bit of a hack here, but hey
        global MAIN_WINDOW
        if filename.split('.')[-2].endswith('vineyard-preferences') or MAIN_WINDOW is None:
            MAIN_WINDOW = self['window']

    def _downgrade_xml(self, xml):
        xml = re.sub(
            r'(?ms)$\s+<child>\s+<object class="GtkSpinner".*?</child>',
            '', xml)
        xml = xml.replace(
            '<requires lib="gtk+" version="2.20"/>',
            '<requires lib="gtk+" version="2.18"/>')
        return xml

    def __getitem__(self, key):
        if key not in self._widgets:
            return self._builder.get_object(key)
        else:
            return self._widgets[key]
    def __setitem__(self, key, value):
        self._widgets[key] = value

def get_main_window():
    return MAIN_WINDOW

def widget_update_position(widget):
    widget.resize(1,1)

class list_view_new_text(gtk.ScrolledWindow):
    """
    Return a Gtk TreeView that acts like a ComboBox.
    The actual widget returned is a ScrolledWindow with custom functions
    resembling the functions of gtk.combo_box_new_text."""
    def __init__(self, header=None, headers=[], items=[], columns=1, use_markup=False, select_multiple=False, text_column=0):
        if columns == 1:
            if header == None:
                column_headers = [""]
            else:
                column_headers = [column_title]
        else:
            if headers == []:
                column_headers = [ "" for i in range(columns) ]
            else:
                column_headers = headers

        self.model_columns = [ str for i in range(columns) ]
        self.text_column = text_column

        self.select_multiple = select_multiple

        gtk.ScrolledWindow.__init__(self)
        self.set_border_width(6)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.model = gtk.ListStore(*self.model_columns)
        fix_model(self.model)
        if len(items):
            self.treeview = gtk.TreeView()
        else:
            self.treeview = gtk.TreeView(self.model)

        if select_multiple:
            self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        else:
            self.treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        self.add(self.treeview)

        self.renderers = []
        self.columns = []
        for column_nr in range(len(self.model_columns)):
            cell_renderer = gtk.CellRendererText()
            self.renderers.append(cell_renderer)
            if use_markup:
                column = gtk.TreeViewColumn(
                    column_headers[column_nr],
                    cell_renderer,
                    markup=column_nr
                )
            else:
                column = gtk.TreeViewColumn(
                    column_headers[column_nr],
                    cell_renderer,
                    text=column_nr
                )

            if column_nr == self.text_column:
                column.set_expand(True)

            self.columns.append(column)
            self.treeview.append_column(column)

        if column_headers == [ "" for i in range(columns) ]:
            self.treeview.set_headers_visible(False)

        if len(items):
            for item in items:
                self.model.append(item)
            self.treeview.set_model(self.model)

        self.treeview.set_search_column(self.text_column)

        if gobject.signal_lookup('changed', self) is 0:
            gobject.signal_new(
                'changed',
                self,
                gobject.SIGNAL_ACTION,
                gobject.TYPE_NONE,
                (
                    gobject.TYPE_OBJECT,
                    gobject.TYPE_PYOBJECT,
                    gobject.TYPE_PYOBJECT
                )
            )

        self.treeview.get_selection().connect_after('changed', self._on_selection_changed)

    def _on_selection_changed(self, selection):
        self.emit('changed', self.treeview, self.get_active(), self.get_active_text())

    def get_active(self):
        if self.select_multiple:
            try:
                return [
                    path[0] for path
                    in self.treeview.get_selection().get_selected_rows()[1]
                ]
            except:
                return None
        else:
            try:
                return treeview_get_selected_path(self.treeview)[0]
            except:
                return None

    def get_active_text(self):
        try:
            model = self.treeview.get_model()
            column = self.text_column
            active = self.get_active()
            if type(active) is not list:
                active = [active]
            return [ model[rownr][column] for rownr in active ]
        except:
            return None

    def append_text(self, item, model=None):
        if model is None:
            model = self.model
        if type(item) in (str, unicode):
            model.append((item,))
        elif len(item) == len(self.model_columns):
            model.append(item)
        else:
            error("Cannot append text item with length different than the \n"+ \
                  "number of columns!\n\tItem: %s\n\tColumns: %s" % (
                      item, len(self.model_columns)
                  ))

    def remove(self, index):
        try:
            del self.treeview.get_model()[index]
        except TypeError:
            return False
        return True

    def remove_by_text(self, text, column=0, startswith=False):
        return model_remove_row_by_string(
            self.treeview.get_model(),
            text,
            column_num=column,
            startswith=startswith
        )

    def clear(self):
        self.model = gtk.ListStore(*self.model_columns)
        fix_model(self.model)
        self.treeview.set_model(self.model)

    def set_from_list(self, list):
        model = gtk.ListStore(*self.model_columns)
        for item in list:
            self.append_text(item, model)
        self.model = model
        fix_model(self.model)
        self.treeview.set_model(self.model)

class list_view_new_icon_and_text(gtk.ScrolledWindow):
    """Return a Gtk TreeView that acts like a ComboBox.
The actual widget returned is a ScrolledWindow with custom functions resembling the functions of gtk.combo_box_new_text."""
    def __init__(self, headers=None, one_header=None, number_of_text_columns=1, text_column=None, ignore_first_column=False, items=[], use_markup=False, select_multiple=False):
        if headers == None:
            column_titles = [""] + [""]*number_of_text_columns
            if one_header == None:
                one_header = True
        else:
            column_titles = headers
            if one_header == None:
                one_header = False
        if len(column_titles) != number_of_text_columns+1:
            raise ValueError("Number of headers doesn't match numbers of columns")

        self.one_header = one_header

        if ignore_first_column:
            self.icon_column = 1
            self.columns = [gobject.TYPE_PYOBJECT, gtk.gdk.Pixbuf] + [str]*number_of_text_columns
        else:
            self.icon_column = 0
            self.columns = [gtk.gdk.Pixbuf] + [str]*number_of_text_columns

        if text_column == None:
            if ignore_first_column:
                self.text_column = 2
            else:
                self.text_column = 1
        else:
            self.text_column = text_column
        self.ignore_first_column = ignore_first_column

        self.select_multiple = select_multiple

        gtk.ScrolledWindow.__init__(self)
        self.set_border_width(0)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.model = gtk.ListStore(*self.columns)
        fix_model(self.model)
        if len(items):
            self.treeview = gtk.TreeView()
        else:
            self.treeview = gtk.TreeView(self.model)

        if select_multiple:
            self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        else:
            self.treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        self.add(self.treeview)

        column = gtk.TreeViewColumn(column_titles[0])
        column.set_resizable(False)
        #column.set_sort_column_id(1)

        self._drag_test_start_function = None
        self._drag_creation_function = None
        self._drag_type = ([("text/uri-list", 0, 1)], gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)

        self.renderers = []
        self.cell_renderer_icon = gtk.CellRendererPixbuf()
        self.renderers.append(self.cell_renderer_icon)
        column.pack_start(self.cell_renderer_icon, False)
        column.set_cell_data_func(self.cell_renderer_icon, cell_data_function_icon_markup_icon, self.icon_column)
        self.treeview.append_column(column)

        if self.one_header:
            column.set_expand(True)

            self.cell_renderer_advanced = CellRendererHeaderText()
            # There's a bug in PyGTK in Ubuntu Natty where pango.ELLIPSIZE_END
            # is None, which it shouldn't be.
            try:
                self.cell_renderer_advanced.set_property("ellipsize", pango.ELLIPSIZE_END)
            except TypeError:
                self.cell_renderer_advanced.set_property("ellipsize", '3')
            self.renderers.append(self.cell_renderer_advanced)

            if ignore_first_column:
                markup_column = 2
            else:
                markup_column = 1

            column.pack_start(self.cell_renderer_advanced, True)
            #column.set_cell_data_func(renderer_app, cell_data_function_icon_markup_markup)
            column.add_attribute(self.cell_renderer_advanced, 'markup', markup_column)
        else:

            for i in range(number_of_text_columns):
                self.renderers.append(gtk.CellRendererText())

                if ignore_first_column:
                    column_nr = i+2
                else:
                    column_nr = i+1

                #if self.one_header:
                #    column.pack_start(self.cell_renderer_advanced, True)
                #else:
                if use_markup:
                    kwargs = {'markup': column_nr}
                    #print "Adding markup header nr %s..." % column_nr
                else:
                    kwargs = {'text': column_nr}
                    #print "Adding text header nr %s..." % column_nr

                #print "\tAdded header '%s'" % column_titles[i+1]
                column = gtk.TreeViewColumn(
                    column_titles[i+1],
                    self.renderers[-1],
                    **kwargs
                )
                self.treeview.append_column(column)

        self.treeview.set_search_column(self.text_column)

        if headers == None:
            self.treeview.set_headers_visible(False)

        if len(items):
            for item in items:
                try:
                    self.model.append(item)
                except TypeError:
                    print "TypeError in adding item to list: %s" % item
            self.treeview.set_model(self.model)

        # Register custom event signals
        if gobject.signal_lookup('changed', self) is 0:
            gobject.signal_new('changed',
                               self, gobject.SIGNAL_ACTION,
                               gobject.TYPE_NONE, (
                                   gobject.TYPE_OBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT))
        if gobject.signal_lookup('right-click', self) is 0:
            gobject.signal_new('right-click',
                               self, gobject.SIGNAL_ACTION,
                               gobject.TYPE_NONE, (
                                   gobject.TYPE_OBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gtk.gdk.Event))
        if gobject.signal_lookup('double-click', self) is 0:
            gobject.signal_new('double-click',
                               self, gobject.SIGNAL_ACTION,
                               gobject.TYPE_NONE, (
                                   gobject.TYPE_OBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_PYOBJECT,
                                   gtk.gdk.Event))

        self.treeview.get_selection().connect_after('changed', self._on_selection_changed)
        self.treeview._drag_start_position = None
        self.treeview.connect('button-press-event', self._on_button_press)
        self.treeview.connect('button-release-event', self._on_button_release)
        self.treeview.connect('motion-notify-event', self._on_motion)
        self.treeview.connect('drag-begin', self._on_drag_begin)
        self.treeview.connect('drag-data-get', self._on_drag_data_get)

    def _on_selection_changed(self, selection):
        if selection.get_mode() == gtk.SELECTION_MULTIPLE:
            path, column = self.treeview.get_cursor()
            selected_row = self.treeview.get_model()[path[0]]
        else:
            path = None
            selected_row = treeview_get_selected_row(self.treeview)

        if not selected_row:
            return False

        if path is None:
            path = selection.get_selected_rows()[1][0]
        selected = unicode(selected_row[self.text_column].split('\n')[0])

        """ If the user clicked a header, select the next non-header row instead """
        if selected.startswith('<header'):
            if path[0]+1 < len(self.treeview.get_model()):
                self.treeview.set_cursor((path[0]+1,))
            else:
                self.treeview.get_selection().unselect_all()
            return False

        if self.ignore_first_column:
            self.emit('changed', self.treeview, self.get_active(), self.get_active_text(column = 0))
        else:
            self.emit('changed', self.treeview, self.get_active(), self.get_active_text())

    def _on_button_press(self, widget, event):
        if event.type not in (
            gtk.gdk.BUTTON_PRESS,
            gtk.gdk._2BUTTON_PRESS
        ):
            return False

        # DND handling
        if event.button == 1:
            widget._drag_start_position = (int(event.x), int(event.y))
        # Double click and menu handling
        if event.button == 3 or event.type == gtk.gdk._2BUTTON_PRESS:
            clicked_nr = clicked_text = None
            x = int(event.x)
            y = int(event.y)
            time = event.time
            clickedpath = self.treeview.get_path_at_pos(x, y)
            if clickedpath != None:
                path, col, cellx, celly = clickedpath
                clickedrow = self.treeview.get_model()[path]

                if not clickedrow[self.text_column].startswith('<header>'):
                    self.treeview.grab_focus()
                    self.treeview.set_cursor( path, col, 0)

                    clicked_nr = path[0]
                    if self.ignore_first_column:
                        clicked_text = clickedrow[0]
                    else:
                        clicked_text = clickedrow[self.text_column]
            # Right click
            if event.button == 3 and event.type == gtk.gdk.BUTTON_PRESS:
                self.emit('right-click',
                          self.treeview,
                          clicked_nr,
                          clicked_text,
                          event)
            # Left double click
            elif event.button == 1 and event.type == gtk.gdk._2BUTTON_PRESS:
                self.emit('double-click',
                          self.treeview,
                          clicked_nr,
                          clicked_text,
                          event)
            return True
        return False

    def _on_button_release(self, widget, event):
        # DND Handling
        if event.button == 1:
            widget._drag_start_position = None
        return False

    def _on_motion(self, widget, event):
        # DND Handling
        if (
            widget._drag_start_position is not None
            and self._drag_test_start_function is not None
            and self._drag_creation_function is not None
        ):
            startx, starty = widget._drag_start_position
            if widget.drag_check_threshold(startx, starty, int(event.x), int(event.y)):
                widget._drag_start_position = None

                path = self.treeview.get_path_at_pos(int(event.x), int(event.y))[0]
                if path != None:
                    row = self.treeview.get_model()[path]
                    if not row[self.text_column].startswith('<header>'):
                        clicked_nr = path[0]
                        if self.ignore_first_column:
                            clicked_text = row[0]
                        else:
                            clicked_text = row[self.text_column]

                        data = self._drag_test_start_function(clicked_nr, clicked_text)

                        if data:
                            if type(data) in (list, tuple):
                                self._drag_data = (data[0], clicked_nr, clicked_text)
                            else:
                                self._drag_data = (clicked_nr, clicked_text)
                            widget.drag_begin(*list(
                                list(self._drag_type)+[1, event]
                            ))
        return True

    def _on_drag_begin(self, widget, context):
        if (
            type(self._drag_data) in (list, tuple) and
            type(self._drag_data[0]) is not int
        ):
            context.set_icon_pixbuf(self._drag_data[0], 0, 0)
        return False

    def _on_drag_data_get(self, widget, context, selection, targetType, eventTime):
        if targetType == 1:
            data = self._drag_creation_function(*self._drag_data[-2:])
            if data:
                selection.set(selection.target, 8, data)

    def set_drag_test_start_function(self, function):
        self._drag_test_start_function = function
    def set_drag_creation_function(self, function):
        self._drag_creation_function = function

    def set_drag_type(self, drag_type):
        self._drag_type = drag_type

    def get_active(self):
        if self.select_multiple:
            try:
                return [ path[0] for path in self.treeview.get_selection().get_selected_rows()[1] ]
            except:
                return None
        else:
            try:
                return treeview_get_selected_path(self.treeview)[0]
            except:
                return None

    def get_active_text(self, column=None):
        if column == None and self.ignore_first_column:
            column = 0
        try:
            model = self.treeview.get_model()
            if column == None:
                column = self.text_column
            active = self.get_active()
            if type(active) != list:
                active = [active]
            if self.select_multiple:
                return [ model[rownr][column] for rownr in active ]
            else:
                return model[active[0]][column]
        except:
            return None

    def get_section_indexes(self):
        section_list = []
        for index, row in enumerate(self.model):
            if '<header' in row[self.text_column]:
                section_list.append((
                    row[self.text_column].split('>')[1].split('<')[0],
                    index
                ))
        return section_list

    def insert_in_section(self, section, items, at_top=False, alphabetically=False):
        print "\nInserting {0} in section \"{1}\"".format(items[2], section)
        section_items = []
        model = self.treeview.get_model()
        for index, row in enumerate(model):
            if len(section_items):
                if '<header' not in row[self.text_column]:
                    section_items.append(int(index)) ## create a copy
                else:
                    break
            else:
                if '<header' not in row[self.text_column]:
                    continue
                if row[self.text_column].split('>')[1].split('<')[0] == section:
                    section_items.append(int(index))
                    ## If we're on the last row, append now
                    if index+1 == len(model):
                        model.append(items)
                        return
        print "\tSection is:", section
        ## If the section was found
        if len(section_items):
            if len(section_items) == 1:
                model.insert_after(
                    model.get_iter((section_items[0],0)),
                    items
                )
                print "\tSection is empty, inserting at top ({0}).".format(section_items[0])
            else:
                if not alphabetically:
                    model.insert_after(
                        model.get_iter((section_items[-1],0)),
                        items
                    )
                    #print "\tNot alphabetically, inserting at end ({0}).".format(section_items[-1])
                else:
                    ## First get a list of the rows in this section
                    current_list = []
                    for index in section_items:
                        current_list.append((
                            model[index][self.text_column],
                            index
                        ))
                    ## Now create a copy of that list and add our row to it
                    ## so we can sort it and compare it to the original
                    current_list = current_list[1:]
                    new_list = list(current_list)
                    new_list.append((items[self.text_column], -1))
                    new_list.sort(key=lambda i: i[0].lower())
                    print "Old list:",current_list
                    print "New list:",new_list
                    ## Go through the two lists and note where they differ
                    ## and add the new row there
                    for index in range(len(new_list)):
                        if index >= len(current_list):
                            model.insert_after(
                                model.get_iter(
                                    (current_list[-1][1],)
                                    ),
                                items
                            )
                            print "Insert after {0}".format(current_list[-1][1])
                        elif current_list[index][0] != new_list[index][0]:
                            model.insert_before(
                                model.get_iter(
                                    (current_list[index][1],)
                                    ),
                                items
                            )
                            print "Insert at {0}".format(current_list[index][1])
                            print "\tAccording to our sort, item inserted at {0} ({1}).".format(current_list[index][1], index)
                            print "\tOld list item was {0}.".format(current_list[index][0])
                            break
        else:
            model.append(items)

    def append(self, items):
        self.model.append(items)

    def append_text(self, items):
        self.model.append([None]+items)

    def append_header(self, title, index=None):
        print "Add header", title
        items = [None, None, '<header>%s</header>' % title]
        if index is not None:
            sections = self.get_section_indexes()
            print "\tExisting headers are:", sections
            if len(sections) and index > 0:
                sections.insert(index, title)
                taken_section_indexes = [i[1] for i in sections if len(i) > 1]
                print ("\tHeader is not first, looking through list of headers "+
                        "for location. Header:"), sections
                for s_index, section in enumerate(sections):
                    if section == title:
                        print "\tFound location for header:", s_index-1
                        if s_index-1 == 0 and s_index-1 not in taken_section_indexes:
                            print "\tLocation is at the beginning, prepend."
                            self.model.prepend(items)
                            break
                        else:
                            self.insert_in_section(
                                sections[s_index-1][0],
                                items
                            )
                            break
            else:
                self.model.prepend(items)
        else:
            self.model.append(items)

    def remove(self, index):
        try:
            del self.treeview.get_model()[index]
        except TypeError:
            return False
        return True

    def remove_by_text(self, text, startswith=False):
        return model_remove_row_by_string(
            self.treeview.get_model(),
            text,
            column_num = self.text_column,
            startswith = startswith)

    def get_row_nr_by_text(self, text, startswith=False, column=None):
        if column == None and self.ignore_first_column:
            column = 0
        return model_get_rownr_from_string(
            self.treeview.get_model(),
            text,
            column_num = column,
            startswith = startswith)

    def clear(self):
        self.model = gtk.ListStore(*self.columns)
        fix_model(self.model)
        self.treeview.set_model(self.model)

    def set_cell_value(self, row, column, value):
        row_iter = self.model.get_iter((row,))
        return self.model.set(row_iter, column, value)

    def set_from_list(self, list):
        model = gtk.ListStore(*self.columns)
        for item in list:
            model.append((item,))
        self.model = model
        fix_model(self.model)
        self.treeview.set_model(self.model)


class new_label_with_widget(gtk.HBox):
    def __init__(self, label="", widget=None):
        gtk.HBox.__init__(self)
        self.label = gtk.Label(label)
        self.label.set_alignment(0.0, 0.5)

        self.pack_start(self.label, True, True)

        if type(widget) in (tuple, list):
            self.widgets = widget

            self.widget = gtk.HBox()
            self.widget.set_spacing(6)

            for widget in self.widgets:
                self.widget.pack_start(widget, False, True)
            self.sizable = self.widgets
        else:
            self.widget = widget
            self.sizable = [self.widget]

        self.pack_start(self.widget, False, True)

def filechooserdialog_new_with_filters(title=None, parent=None, file_types=None, filters=[filefilters['all']], default_filter='all', on_response_func=None, action=gtk.FILE_CHOOSER_ACTION_OPEN, buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OK, gtk.RESPONSE_OK), preview_type=None, backend=None):
    dialog = gtk.FileChooserDialog(title=title,
                                   parent=parent,
                                   action=action,
                                   buttons=buttons,
                                   backend=None)
    dialog.set_icon_name('vineyard-preferences')
    if action not in (gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER):
        """ If we got the shorthand version of the arguments, set the remaining args """
        if file_types != None:
            filters = [ filefilters[i] for i in file_types ]
            if 'images' in file_types or 'windows_executables_and_images' in file_types:
                preview_type = 'windows_executables_and_images'
            else:
                preview_type = 'windows_executables'
        """ Setup the filter and preview widget """
        for f in filters:
            dialog.add_filter(f)
        dialog.set_filter(filefilters[default_filter])
        if preview_type in filechooser_previews:
            image = gtk.Image()
            dialog.set_preview_widget(image)
            dialog.connect('selection_changed', filechooser_previews[preview_type])
    if on_response_func != None:
        dialog.connect('response', on_response_func)
    return dialog

def widget_get_top_parent(widget):
    parent = widget.get_parent()
    while parent != None:
        parent = parent.get_parent()
    return parent

def frame_wrap(widget, label_text):
    #vbox = gtk.VBox()
    #vbox.set_border_width(6)
    frame = gtk.Frame(label_text)
    frame.set_label_align(0.0, 0.5)
    frame.get_label_widget().set_padding(0, 0)
    frame.get_label_widget().set_markup('<b>%s</b>' % frame.get_label_widget().get_text())
    frame.set_shadow_type(gtk.SHADOW_NONE)
    #vbox.pack_start(frame, expand=True, fill=True)
    alignment = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
    alignment.set_padding(3, 0, 12, 0)
    alignment.add(widget)
    frame.add(alignment)
    alignment.show()
    frame.show()
    #vbox.show()
    #return vbox
    return frame

def button_new_with_image(image, label=None, use_underline=True, icon_size = gtk.ICON_SIZE_BUTTON):
    """
        Return a button containing an hbox with two children: an image and a label.
        label can be either a string or a gtk.Label.
        image can be a gtk.Image, a gtk.Pixbuf, a gtk.STOCK_ value or an icon name.
    """
    button = gtk.Button(label=None, stock=None, use_underline=use_underline)
    hbox = gtk.HBox(spacing=6)
    button.add(hbox)

    if type(image) != gtk.Image:
        icon = image
        image = gtk.Image()
        if type(icon) == gtk.gdk.Pixbuf:
            image.set_from_pixbuf(icon)
        elif icon_name_is_stock(icon):
            icon_set = button.get_style().lookup_icon_set(icon)
            image.set_from_icon_set(icon_set, icon_size)
        else:
            pixbuf = pixbuf_new_from_string(icon, icon_size, widget=button)
            image.set_from_pixbuf(pixbuf)

    image.set_alignment(1.0, 0.5)
    hbox.pack_start(image, expand=True, fill=True)

    if label != None:
        if type(label) != gtk.Widget:
            label = gtk.Label(label)

        label.set_alignment(0.0, 0.5)
        hbox.pack_start(label, expand=True, fill=True)

        label.set_use_underline(use_underline)
        button.set_use_underline(use_underline)

    return button

def widget_get_char_width(widget):
    pango_context = widget.get_pango_context()
    return int(pango.PIXELS(
        pango_context.get_metrics(
            pango_context.get_font_description()
            ).get_approximate_char_width()))

def widget_get_char_height(widget):
    """
    Return maximum height in pixels of a single character.
    We create a Pango Layout, put in a line of lowercase+uppercase letters
    and read the height of the line."""
    pango_layout = pango.Layout(widget.get_pango_context())
    pango_layout.set_text(sys.modules['string'].ascii_letters)
    extents = pango_layout.get_line(0).get_pixel_extents()
    return int(extents[0][3] - extents[0][1])

def widget_get_child_of_type(widget, child_type):
    def _get_child_of_type(widget, child_type):
        children = widget.get_children()
        for child in children:
            if type(child) == child_type:
                return child

    if getattr(widget, 'get_children'):
        if type(child_type) in (list, tuple):
            child_types = child_type
            parent = widget
            for child_type in child_types:
                parent = _get_child_of_type(parent, child_type)
            return parent
        else:
            return _get_child_of_type(widget, child_type)


def widget_get_children_of_type(widget, child_type):
    found_children = []
    try:
        for child in widget.get_children():
            if type(child) == child_type:
                found_children.append(child)
            sub_children = widget_get_children_of_type(child, child_type)
            for found_child in sub_children:
                found_children.append(found_child)
    except AttributeError:
        pass
    return found_children

def fix_filechooserdialog(widget):
    for treeview in widget_get_children_of_type(widget, gtk.TreeView):
        fix_model(treeview.get_model())

def fix_model(model):
    if gobject.signal_lookup('row-has-child-toggled', model) != 0:
        model.connect('row-has-child-toggled', lambda *args: True)
        #model.stop_emission('row-has-child-toggled')


#def GtkGetPathFromString(widget, string, pos=0, startswith=False):
def model_get_rownr_from_string(model, string, column_num=0, startswith=False):
    """Return row nr. of string"""
    if type(string) in (str, unicode):
        string = '%s' % string.lower()
    for row in iter(model):
        row_value = row[column_num]
        if type(row_value) in (str, unicode):
            row_value = '%s' % row_value.lower()
            if (
                row_value == string
               or (startswith and row_value.startswith(string))
            ):
                return row.path[0]
        else:
            if row_value == string:
                return row.path[0]
    return None

def model_remove_row_by_string(model, string, column_num=0, startswith=False):
    if type(string) in (tuple, list):
        strings = string
    else:
        strings = [string]
    return_value = True
    for string in strings:
        path = model_get_rownr_from_string(model, string, column_num=column_num, startswith=startswith)
        if path == None:
            return_value = False
        else:
            del model[path]
    return return_value

def combobox_get_active_value(combobox, column=0):
    return combobox.get_model()[combobox.get_active()][column]

def combobox_set_active_by_string(combobox, string, startswith=False):
    rownr = model_get_rownr_from_string(combobox.get_model(), string, startswith=startswith)
    if rownr != None:
        combobox.set_active(rownr)
    else:
        raise KeyError("Could not set active item: String not found: %s" % string)
    return True

def treeview_set_cursor_by_string(treeview, string):
    rownr = model_get_rownr_from_string(treeview.get_model(), string)
    if rownr != None:
        treeview.set_cursor((rownr,))
    else:
        raise KeyError("Could not set cursor: String not found: %s" % string)
    return True

#def GtkGetSelectedPathInTreeview(treeview):
def treeview_get_selected_path(treeview):
    if treeview.get_selection().get_selected()[1] == None:
        return None
    return treeview.get_model().get_path(treeview.get_selection().get_selected()[1])

#def GtkGetSelectedInTreeview(treeview):
def treeview_get_selected_row(treeview):
    if treeview.get_selection().get_mode() == gtk.SELECTION_MULTIPLE:
        raise TypeError, 'treeview_get_selected_row can not be used when selection mode is gtk.SELECTION_MULTIPLE'
        return None
    else:
        path = treeview_get_selected_path(treeview)
        if path == None:
            return None
        return treeview.get_model()[path]

#def GtkSetSelectedRowItem(treeview, pos, value):
def treeview_set_column_in_selected_row(treeview, column_num, value):
    path = treeview_get_selected_path(treeview)
    if path == None:
        return False
    treeview.get_model()[path][column_num] = value
    return True

def treeview_remove_selected_row(treeview):
    path = treeview_get_selected_path(treeview)
    if path == None:
        return False
    del treeview.get_model()[path]
    return True

def row_separator_function(model, iter):
    return model.get_value(iter,0) == '-'

def cell_data_function_icon_markup_icon(column, cell, model, iter, icon_column=0):
    icon = model.get_value(iter, icon_column)
    markup = model.get_value(iter, icon_column+1)
    cell.set_property("pixbuf", icon)
    if markup.startswith('<header') and markup.endswith('</header>'):
        cell.set_property("visible", False)
    else:
        cell.set_property("visible", True)

def cell_data_function_icon_markup_markup(column, renderer, model, iter, markup_column=1):
    markup = model.get_value(iter, markup_column)
    if markup.startswith('<header') and markup.endswith('</header>'):
        #print renderer.get_fixed_size()
        #padding = int(renderer.get_fixed_size()[1] / 4)
        #renderer.set_property('ypad', padding)
        #renderer.set_property('yalign', 0.625)
        markup = '<'.join('>'.join(markup.split('>')[1:]).split('<')[:-1])
        markup = '<b>%s</b>' % markup
        #renderer.set_property('cell-background-gdk', styles['treeview'].bg[gtk.STATE_NORMAL])
        #renderer.set_property('foreground-gdk', styles['treeview'].fg[gtk.STATE_NORMAL])
    #else:
        #renderer.set_property('cell-background-set', False)
        #renderer.set_property('foreground-set', False)
    renderer.set_property("markup", markup)


def filechooser_preview_windows_executables(filechooser):
    _filechooser_preview_windows_executables_and_or_images(filechooser, True)

def filechooser_preview_windows_executables_and_images(filechooser):
    _filechooser_preview_windows_executables_and_or_images(filechooser, False)

def _filechooser_preview_windows_executables_and_or_images(filechooser, only_programs=False):
    filename = filechooser.get_preview_filename()
    if filename and os.path.isfile(filename):
        pixbuf = pixbuf_new_from_any_file(filename)
        if pixbuf == None:
            filechooser.set_preview_widget_active(False)
        else:
            filechooser.get_preview_widget().set_from_pixbuf(pixbuf)
            filechooser.set_preview_widget_active(True)
    else:
        filechooser.set_preview_widget_active(False)

filechooser_previews = {
    'windows_executables': filechooser_preview_windows_executables,
    'windows_executables_and_images': filechooser_preview_windows_executables_and_images
}

def widget_set_loading(widget):
    widget_loading = gtk.HBox()
    widget_loading_vbox = gtk.VBox()
    widget_loading_spinner = gtk.Image()
    widget_loading_spinner.set_from_pixbuf(pixbuf_new_from_string('gnome-spinner', widget=widget_loading_spinner))
    widget_loading_vbox.pack_start(widget_loading_spinner)
    widget_loading.pack_start(widget_loading_vbox)


def pixbuf_new_from_program_data(program, size=32, force_update=False):
    if type(size) != int:
        size = gtk.icon_size_lookup(size)[1]
    # Fill the programs listview
    icon = wine.programs.getIcon(program, force_update=force_update)
    #self.debug("Icon lookup for \"%s\" returns \"%s\"." % (info['name'], icon))
    if icon != None:
        icon = wine.icons.convert(icon)
        if icon != None:
            if type(icon) == list:
                """ Manual icon replacement for script files """
                if icon == ['text-x-generic'] and 'programexe' in program and program['programexe'].lower().endswith('.bat'):
                    icon = gtk.icon_theme_get_default().load_icon('text-x-script', size, 0)
                else:
                    for iconname in icon:
                        try:
                            icon = gtk.icon_theme_get_default().load_icon(iconname, size, 0)
                            break
                        except glib.GError:
                            continue
            else:
                try:
                    icon = gtk.gdk.pixbuf_new_from_file_at_size(icon, size,size)
                except glib.GError:
                    warning("Tried to read \"%s\" as an icon and failed." % icon)
                    pass
    if icon == None:
        #self.debug("\tIcon lookup returned nothing.")
        try:
            icon = gtk.icon_theme_get_default().load_icon("application-x-ms-dos-executable", size, 0)
        except glib.GError:
            icon = gtk.icon_theme_get_default().load_icon("application-x-executable", size, 0)
            #self.debug("\tUsing template icon.")
    return icon

def pixbuf_new_from_any_file(filename, size=None):
    import wine
    try:
        os.remove(os.path.realpath(
            "{0}/../.icons/wine-application-icon-vineyard-filepreview.png".format(
                wine.common.ENV['WINEPREFIX']
            )
        ))
    except OSError:
        pass
    icon_file = wine.programs.get_icon({'name': 'vineyard-filepreview', 'icon': filename}, force_update=True)
    if icon_file == None:
        return None
    else:
        try:
            if size == None:
                return gtk.gdk.pixbuf_new_from_file(icon_file)
            else:
                return gtk.gdk.pixbuf_new_from_file_at_size(icon_file, size,size)
        except glib.GError:
            return None

def icon_name_is_stock(icon_name):
    # We use getattr here since we need to read the variable's string value
    return icon_name in [
        getattr(gtk, i)
        for i in dir(gtk)
        if i.startswith('STOCK_')
    ]

def icon_names_usable(icon_names):
    if type(icon_names) != list:
        icon_names = [ icon_names ]

    icon_theme_icon_list = gtk.icon_theme_get_default().list_icons()
    return [
        icon for icon in icon_names
        if icon in icon_theme_icon_list
    ]

def pixbuf_new_from_string(icon, icon_size=gtk.ICON_SIZE_BUTTON, widget=None, return_first=False):
    if type(icon) == list:
        icons = []
        for i in icon:
            icons.append(pixbuf_new_from_string(i, icon_size=icon_size, widget=widget))
        if return_first:
            icons = [ i for i in icons if i != None ]
            if len(icons):
                return icons[0]
            else:
                return None
        else:
            return icons

    pixbuf = None
    if type(icon) == gtk.gdk.Pixbuf:
        return icon
    elif type(icon) == str:
        """ See if this is a gtk.STOCK_ value """
        if icon_name_is_stock(icon):
            destroy = False
            if widget == None:
                destroy = True
                """ We need a widget to get the style to look up a stock icon
                    and HBox seems to be the simplest widget available. """
                widget = gtk.HBox()
            pixbuf = widget.render_icon(icon, gtk.ICON_SIZE_BUTTON)
            if destroy:
                widget.destroy()
        else:
            height = gtk.icon_size_lookup(icon_size)[1]
            try:
                pixbuf = gtk.icon_theme_get_default().load_icon(icon, height, 0)
            except glib.GError:
                pass

    if pixbuf == None:
        #error("Couldn't lookup icon by the name \"%s\"." % icon)
        return None
    else:
        return pixbuf

def pixbuf_from_widget(widget):
    widget.window.process_updates(True)
    x, y, width, height, bit_depth = widget.window.get_geometry()
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, width, height)
    pixbuf.get_from_drawable(widget.window,
                             widget.window.get_colormap(),
                             0, 0, 0, 0, width, height)
    return pixbuf

def escape_xml(string):
    return string.replace('<','&lt;').replace('>','&gt;')

def dict_keys_to_unicode(dictionary):
    """ Return a copy of the given dict with all keys in unicode """
    if type(dictionary) == dict:
        return dict((unicode(k), v) for (k, v) in dictionary.iteritems())
    else:
        raise TypeError, "First argument should be a dictionary."

def in_list_caseinsensitive(item, list, startswith=False):
    item = item.lower()
    for i in iter(list):
        if (item == i.lower()) \
           or (startswith and i.lower().startswith(item)):
            return True
    return False

def thread_start(function, args=(), kwargs={}):
    thread = threading.Thread(target=function, args=args, kwargs=kwargs)
    thread.start()

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

def gdk_color_to_hex(gdk_color):
    try:
        return str(gdk_color)
    except:
        return '#{r}{g}{b}'.format(
            r = str(hex(int((gdk_color.red/65535.)*255)))[-2:],
            g = str(hex(int((gdk_color.green/65535.)*255)))[-2:],
            b = str(hex(int((gdk_color.blue/65535.)*255)))[-2:]
    )
def gdk_color_to_float(gdk_color):
    return gdk_color.red/65535., gdk_color.green/65535., gdk_color.blue/65535.

def gdk_color_mix(first_color, second_color, mix=0.5):
    return gtk.gdk.Color(
        int(min(65535, (first_color.red*(1.0-mix)) + (second_color.red*mix))),
        int(min(65535, (first_color.green*(1.0-mix)) + (second_color.green*mix))),
        int(min(65535, (first_color.blue*(1.0-mix))  + (second_color.blue*mix))))

def set_loading_overlay(widget, state=True):
    def _expose_event(widget, event):
        if widget.window == None:
            return False
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
    if widget.window != None:
        widget.window.invalidate_rect(gtk.gdk.Rectangle(0,0, widget.allocation.width, widget.allocation.height), True)
        widget.window.process_updates(True)

class CellRendererHeaderText(gtk.GenericCellRenderer):
    __gproperties__ = {
        'text': (gobject.TYPE_STRING, 'text', 'text displayed', '', gobject.PARAM_READWRITE),
        'markup': (gobject.TYPE_STRING, 'markup', 'markup', '', gobject.PARAM_READWRITE),
        'ellipsize': (gobject.TYPE_STRING, 'ellipsize', 'ellipsize', '', gobject.PARAM_READWRITE)
    }

    property_names = __gproperties__.keys()

    def __init__(self):
        self.__gobject_init__()

    def __getattr__(self, name):
        try:
            return self.get_property(name)
        except TypeError:
            raise AttributeError

    def __setattr__(self, name, value):
        try:
            self.set_property(name, value)
        except TypeError:
            self.__dict__[name] = value

    def do_get_property(self, property):
        if property.name not in self.property_names:
            raise TypeError('No property named %s' % (property.name,))
        return self.__dict__[property.name]

    def do_set_property(self, property, value):
        if property.name not in self.property_names:
            raise TypeError('No property named %s' % (property.name,))
        self.__dict__[property.name] = value

    def on_render(self, window, widget, bg_area, cell_area, exp_area, flags):
        self.draw_header = False
        self.draw_header_line = True
        x_offset, y_offset, width, height = self.on_get_size(widget, cell_area)
        layout = self.get_layout(widget)

        # Determine state to get text color right.
        if flags & gtk.CELL_RENDERER_SELECTED:
            if widget.get_property('has-focus'):
                state_type = gtk.STATE_SELECTED
            else:
                state_type = gtk.STATE_ACTIVE
        else:
            state_type = gtk.STATE_NORMAL

        widget.style.paint_layout(
            window, state_type, True, cell_area, widget, 'text',
            cell_area.x + x_offset, cell_area.y + y_offset, layout)

        if self.draw_header:
            """ Draw an arrow at the fair right (our style) """
            widget.style.paint_arrow(
                window, state_type, gtk.SHADOW_OUT, cell_area, widget, 'arrow',
                gtk.ARROW_DOWN, False,
                cell_area.width - x_offset - cell_area.height/2,
                cell_area.y + (cell_area.height/2)/2,
                cell_area.height/2, cell_area.height/2)
            """ Draw a line at the top of the row """
            if self.draw_header_line:
                line_color = gdk_color_mix(styles['treeview'].bg[gtk.STATE_NORMAL], styles['treeview'].fg[gtk.STATE_NORMAL], mix=0.1)
                gc = window.new_gc()
                gc.set_rgb_fg_color(line_color)
                window.draw_line(gc, cell_area.x, cell_area.y, cell_area.width, cell_area.y)
            """ Draw an expander at the far right (Rhythmbox style)
             Disabled since we don't support (de)expanding (yet?) """
            """expander_size = widgetsizes['expander']
            widget.style.paint_expander(
                window, state, cell_area, widget, '',
                #cell_area.width-x_offset, cell_area.y+y_offset), gtk.EXPANDER_EXPANDED
                cell_area.width - x_offset - expander_size[0],
                cell_area.y + y_offset + expander_size[1] / 2,
                gtk.EXPANDER_EXPANDED)"""

    def get_layout(self, widget):
        '''Gets the Pango layout used in the cell in a TreeView widget.'''
        layout = pango.Layout(widget.get_pango_context())
        layout.set_width(-1)    # Do not wrap text.

        if self.markup:
            if self.markup.startswith('<header') and self.markup.endswith('</header>'):
                self.draw_header = True
                if self.markup.startswith('<header first>'):
                    self.draw_header_line = False
                self.markup = '<'.join('>'.join(self.markup.split('>')[1:]).split('<')[:-1])
                self.markup = '<b>%s</b>' % self.markup

        if self.markup:
            layout.set_markup(self.markup)
        else:
            layout.set_markup('')

        return layout

    def on_get_size(self, widget, cell_area):
        # The following size calculations have tested so that the TextView
        # will fully fit in the cell when editing and it will be the same
        # size as a CellRendererText cell with same amount or rows.
        xpad = 2
        ypad = 2

        xalign = 0
        yalign = 0.5

        layout = self.get_layout(widget)
        width, height = layout.get_pixel_size()

        x_offset = xpad
        y_offset = ypad

        if cell_area:
            x_offset = xalign * (cell_area.width - width)
            x_offset = max(x_offset, xpad)
            x_offset = int(round(x_offset, 0))

            y_offset = yalign * (cell_area.height - height)
            y_offset = max(y_offset, ypad)
            y_offset = int(round(y_offset, 0))

        width  = width  + (xpad * 2)
        height = height + (ypad * 2)

        return x_offset, y_offset, width, height

gobject.type_register(CellRendererHeaderText)
