#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#

import gobject, gtk, pango
import vineyard

class SimpleList(gtk.VBox):
    def __init__(self, headers=None, rows=None, types=None, combos=None, combotypes=None, selection_type=None):
        if gobject.signal_lookup('toggled', self) == 0:
            gobject.signal_new(
                "toggled",
                self,
                gobject.SIGNAL_ACTION,
                gobject.TYPE_NONE,
                (
                    gobject.TYPE_PYOBJECT,
                    gobject.TYPE_PYOBJECT,
                    gobject.TYPE_PYOBJECT
                ))
        if gobject.signal_lookup('changed', self) == 0:
            gobject.signal_new(
                "changed",
                self,
                gobject.SIGNAL_ACTION,
                gobject.TYPE_NONE,
                (
                    gobject.TYPE_PYOBJECT,
                    gobject.TYPE_PYOBJECT,
                    gobject.TYPE_PYOBJECT
                ))
        if gobject.signal_lookup('right-click', self) == 0:
            gobject.signal_new(
                'right-click',
                self, gobject.SIGNAL_ACTION,
                gobject.TYPE_NONE,
                (
                    gobject.TYPE_OBJECT,
                    gobject.TYPE_PYOBJECT,
                    gobject.TYPE_PYOBJECT,
                    gtk.gdk.Event
                ))
        if gobject.signal_lookup('double-click', self) == 0:
            gobject.signal_new(
                'double-click',
                self, gobject.SIGNAL_ACTION,
                gobject.TYPE_NONE,
                (
                    gobject.TYPE_OBJECT,
                    gobject.TYPE_PYOBJECT,
                    gobject.TYPE_PYOBJECT,
                    gtk.gdk.Event
                ))
        self._fallback_pixbuf = None

        # Remember: First cell is index
        if rows is None:
            rows = []

        if len(rows):
            self.rows = self.__failsafe_rows(rows)
            if types is None:
                self._cell_types, self._render_types = self.__convert_rows_to_types(self.rows)
            else:
                self._cell_types, self._render_types = self.__convert_rows_to_types([types])
        elif types is not None:
            self.rows = rows
            self._cell_types, self._render_types = self.__convert_rows_to_types([types])
        else:
            raise(ValueError, "You need to supply either rows or types.")

        number_of_combocols = len([
            col for col in self._cell_types
            if col is list
        ])
        if combos is not None:
            if type(combos[0][0]) not in (tuple, list):
                self._combos = [
                    [
                        [row] for row in combo
                    ]
                    for combo
                    in combos
                ]
            else:
                self._combos = combos
            if combotypes is not None:
                self._combocols = combotypes
            else:
                self._combocols = []
                for combo in self._combos:
                    if type(combo[0]) in (list, tuple):
                        self._combocols.append([str] * len(combo[0]))
                    else:
                        self._combocols.append([str])
            self._combomodels = [
                gtk.ListStore(*column)
                for column
                in self._combocols
            ]
            for combo_nr, combo in enumerate(self._combos):
                for row in combo:
                    self._combomodels[combo_nr].append(
                        self._create_model_row_from_row(row, self._combocols[combo_nr])
                    )
        else:
            if number_of_combocols:
                raise(ValueError, "When using Combo renderers, you need to assign the comborows.")

        if headers is None:
            headers = [ '' for i in range(len(self._cell_types)-1) ]

        self.headers = headers

        self.selection_type = selection_type

        gtk.VBox.__init__(self)

        self._create_widgets()
        self._create_headers()
        self.fill()

    def _create_widgets(self):
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_border_width(0)
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.pack_start(self.scrolled_window, expand=True, fill=True)

        self.treeview = gtk.TreeView()
        self.scrolled_window.add(self.treeview)

        self.model = gtk.ListStore(*self._cell_types)
        self.treeview.set_model(self.model)

        if self.selection_type is None:
            self.treeview.get_selection().set_mode(gtk.SELECTION_NONE)
        elif self.selection_type == 'single':
            self.treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
        elif self.selection_type == 'multiple':
            self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        self.show_all()

        self.treeview._drag_start_position = None
        self.treeview.connect('button-press-event', self.__on_button_press)
        self.treeview.connect('button-release-event', self.__on_button_release)
        self.treeview.connect('motion-notify-event', self.__on_motion)
        self.treeview.connect('drag-begin', self.__on_drag_begin)
        self.treeview.connect('drag-data-get', self.__on_drag_data_get)

    def get(self):
        return list(self.iter())

    def iter(self):
        return (
            [ col for col in row ]
            for row in self.model
        )

    def set(self, data, index=None, row=None, column=None):
        if index is None and row is None and column is None:
            return self.fill(rows = data)

        ## Don't go by row (nr), find by index
        if index is not None:
            for row, _row in enumerate(self.model):
                if _row[0] == index:
                    break

        if column is None:
            self.model[row] = data
        else:
            self.model[row][column] = data

    def add(self, rows=None, clear=False):
        if rows is None:
            rows = self.rows
        else:
            # If this is clearly not a list of rows, but a column, use it as such
            if type(rows[0]) not in (list, tuple):
                rows = [rows]

        if clear:
            self.model.clear()

        for row in rows:
            cells = self._create_model_row_from_row(row, self._cell_types)
            # Change model value from combo's index to combo's text
            combo_nr = 0
            for col_nr, render_type in enumerate(self._render_types):
                if render_type == 'combo':
                    if len(self._combos[combo_nr][cells[col_nr]]) > 1:
                        cells[col_nr] = self._combos[combo_nr][cells[col_nr]][1]
                    else:
                        cells[col_nr] = self._combos[combo_nr][cells[col_nr]][0]
                    combo_nr += 1
            self.model.append(cells)

    def fill(self, rows=None):
        return self.add(rows=rows, clear=True)

    def clear(self):
        return self.model.clear()


    def _create_model_row_from_row(self, row, types):
        cells = []
        if type(row) in (list, tuple):
            for index, cell in enumerate(row):
                if types[index] is gtk.gdk.Pixbuf:
                    pixbuf = vineyard.pixbuf_new_from_string(cell)
                    if pixbuf:
                        cells.append(pixbuf)
                    else:
                        cells.append(self._fallback_pixbuf)
                elif type(cell) is list:
                    cells.append(cell[0])
                else:
                    cells.append(cell)
        else:
            cells.append(row)
        return cells

    def set_fallback_pixbuf(self, pixbuf_or_name):
        if type(pixbuf_or_name) in (str, unicode):
            self._fallback_pixbuf = vineyard.pixbuf_new_from_string(pixbuf_or_name)
        else:
            self._fallback_pixbuf = pixbuf_or_name

    def _create_headers(self):
        self.columns = []
        for header_title in self.headers:
            self.columns.append(
                gtk.TreeViewColumn(header_title)
            )
            self.columns[-1].set_resizable(True)
            self.treeview.append_column(self.columns[-1])

        self.renderers = []
        combo_nr = 0
        for column_nr, render_type in enumerate(self._render_types):
            ## Skip first column, it is index
            if column_nr == 0:
                continue

            if render_type == 'toggle':
                self.renderers.append(
                    gtk.CellRendererToggle()
                )
                self.columns[column_nr-1].pack_start(self.renderers[-1])
                self.columns[column_nr-1].add_attribute(self.renderers[-1],
                                                        'active', column_nr)
                self.renderers[-1].set_property('activatable', True)
                self.renderers[-1].connect('toggled', self._toggled, column_nr)
                ## Turn of selection if we can toggle stuff, they are confusing
                ## together, if the user does not want this, set it manually
                ## Only do it if we don't have a combo column though, otherwise
                ## that one won't work
                if 'combo' not in self._render_types:
                    self.treeview.get_selection().set_mode(gtk.SELECTION_NONE)
            elif render_type == 'pixbuf':
                self.renderers.append(
                    gtk.CellRendererPixbuf()
                )
                self.columns[column_nr-1].pack_start(self.renderers[-1])
                self.columns[column_nr-1].add_attribute(self.renderers[-1],
                                                        'pixbuf', column_nr)
            elif render_type == 'combo':
                self.renderers.append(
                    gtk.CellRendererCombo()
                )
                self.renderers[-1].set_property('ellipsize', pango.ELLIPSIZE_END)
                self.renderers[-1].set_property('model', self._combomodels[combo_nr])
                if len(self._combocols[combo_nr]) > 1:
                    self.renderers[-1].set_property('text-column', 1)
                else:
                    self.renderers[-1].set_property('text-column', 0)
                self.renderers[-1].set_property('editable', True)
                self.renderers[-1].set_property('has-entry', False)
                self.renderers[-1].connect('changed', self._combo_changed, column_nr, combo_nr)
                self.columns[column_nr-1].pack_start(self.renderers[-1])
                self.columns[column_nr-1].add_attribute(self.renderers[-1],
                                                        'text', column_nr)
                self.columns[column_nr-1].set_expand(True)
                combo_nr += 1
            else:
                self.renderers.append(
                    gtk.CellRendererText()
                )
                self.renderers[-1].set_property('ellipsize', pango.ELLIPSIZE_END)
                self.columns[column_nr-1].pack_start(self.renderers[-1])
                self.columns[column_nr-1].add_attribute(self.renderers[-1],
                                                      'markup', column_nr)
                self.columns[column_nr-1].set_expand(True)

        if any(self.headers):
            self.treeview.set_headers_visible(True)
        else:
            self.treeview.set_headers_visible(False)

    def _toggled(self, renderer, row, column_nr):
        self.model[row][column_nr] = not self.model[row][column_nr]
        self.emit('toggled', row, column_nr, self.model[row][column_nr])

    def _combo_changed(self, combo, path, combo_iter, column_nr, combo_nr):
        row = path[0]
        if len(self._combocols[combo_nr]) > 1:
            combo_text = combo.get_property('model').get_value(combo_iter, 1)
        else:
            combo_text = combo.get_property('model').get_value(combo_iter, 0)
        combo_active = combo.get_property('model').get_path(combo_iter)[0]

        self.model[row][column_nr] = combo_text

        self.emit('changed', row, column_nr, combo_active)

    def __failsafe_rows(self, rows):
        new_rows = []
        max_row_length = max(*[ len(row) for row in rows ])

        for row in rows:
            # Make sure each row has the same amount of cells
            # adding empty cells to short rows
            new_rows.append(
                row + [ '' for i in range(max_row_length) ][len(row):]
            )
        return new_rows

    def __convert_rows_to_types(self, rows):
        cell_types = []
        render_types = []
        for cell in rows[0]:
            if cell in (str, unicode) or type(cell) in (str, unicode):
                cell_types.append(gobject.TYPE_STRING)
                render_types.append('text')
            elif cell is int or type(cell) is int:
                cell_types.append(gobject.TYPE_INT)
                render_types.append('text')
            elif cell is float or type(cell) is float:
                cell_types.append(gobject.TYPE_FLOAT)
                render_types.append('text')
            elif cell is bool or type(cell) is bool:
                cell_types.append(gobject.TYPE_BOOLEAN)
                render_types.append('toggle')
            elif cell in (tuple, list) or type(cell) in (tuple, list):
                cell_types.append(gobject.TYPE_STRING)
                render_types.append('combo')
            else:
                cell_types.append(gtk.gdk.Pixbuf)
                render_types.append('pixbuf')
        return cell_types, render_types


    def __on_button_press(self, widget, event):
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

    def __on_button_release(self, widget, event):
        # DND Handling
        if event.button == 1:
            widget._drag_start_position = None
        return False

    def __on_motion(self, widget, event):
        # DND Handling
        if (
            widget._drag_start_position is not None
            and self.__drag_test_start_function is not None
            and self.__drag_creation_function is not None
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

                        data = self.__drag_test_start_function(clicked_nr, clicked_text)

                        if data:
                            if type(data) in (list, tuple):
                                self.__drag_data = (data[0], clicked_nr, clicked_text)
                            else:
                                self.__drag_data = (clicked_nr, clicked_text)
                            widget.drag_begin(*list(
                                list(self.__drag_type)+[1, event]
                            ))
        return True

    def __on_drag_begin(self, widget, context):
        if (
            type(self.__drag_data) in (list, tuple) and
            type(self.__drag_data[0]) is not int
        ):
            context.set_icon_pixbuf(self.__drag_data[0], 0, 0)
        return False

    def __on_drag_data_get(self, widget, context, selection, targetType, eventTime):
        if targetType == 1:
            data = self.__drag_creation_function(*self.__drag_data[-2:])
            if data:
                selection.set(selection.target, 8, data)

    def set_drag_test_start_function(self, function):
        self.__drag_test_start_function = function
    def set_drag_creation_function(self, function):
        self.__drag_creation_function = function

    def set_drag_type(self, drag_type):
        self.__drag_type = drag_type
