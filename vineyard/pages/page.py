#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#

import os
import gobject, gtk
import vineyard

class VineyardPage(vineyard.async.ThreadedClass):
    def __init__(self, name="---", icon='gtk-discard', widgets=None, pages=None):
        self.name = name
        self.icon = icon
        self.gobject = gobject.GObject()
        self.gobject.loading = False
        self.gobject.number_of_settings = 0
        self.widget = gtk.VBox()
        self.widget.show()
        self.widgets = None
        self._widgets = widgets
        self._pages = pages

    def _build_widgets(self):
        """Actually build the widgets on the page."""
        self.widgets = []
        if self._widgets != None:
            self.__auto_build_interface(self._widgets)
        elif self._pages != None:
            self.__auto_build_pages(self._pages)

    def _get_widgets(self, get_all=False):
        if get_all:
            if len(self.widgets) and type(self.widgets[0]) == list:
                widgets = []
                for page in self.widgets:
                    for widget in page:
                        widgets.append(widget)
                return widgets
            else:
                return self.widgets
        else:
            if len(self.widgets) and type(self.widgets[0]) == list:
                return self.widgets[self.notebook.get_current_page()]
            else:
                return self.widgets

    def reset(self):
        self.gobject.loading = False
        if self.widgets is None:
            self._build_widgets()
        for widget in self._get_widgets(get_all=True):
            widget.reset()

    def _setup_widget(self, widget_class, size_group=None):
        widget = widget_class.Widget()
        if 'sizable' in dir(widget):
            for child_widget in widget.sizable:
                if size_group is None:
                    size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
                size_group.add_widget(child_widget)
        if not widget.hidden_on_load:
            widget.show()
        widget.gobject.connect('loading-settings', self._loading_settings)
        widget.gobject.connect('settings-loaded', self._settings_loaded)
        widget.gobject.connect('settings-changed', self._settings_changed)
        #widget.gobject.connect('show-page', self._show_page)
        widget.connect('show', self._child_show)
        widget.connect('hide', self._child_hide)
        #self.widgets.append(widget)

        if size_group == None:
            return widget
        else:
            return widget, size_group

    def show_page(self, *args):
        """Builds the widgets (if needed) and sets them up."""
        if self.widgets is None:
            self._build_widgets()
        for widget in self._get_widgets(get_all=False):
            widget.__configure__()

    def _evaluate_visibility_from_children(self, parent, children):
        if len([ i for i in children if not i.hidden_on_load ]):
            parent.show()
        else:
            parent.hide()

    def _build_frames_with_vbox(self, sections):

        def __create_child_and_add_to_container(child, container, parent, size_group=None):
            if size_group is not None:
                child_widget = self._setup_widget(child, size_group)
            else:
                child_widget = self._setup_widget(child)
            if type(child_widget) == tuple:
                child_widget, size_group = child_widget

            if 'widget_should_expand' in dir(child_widget) and child_widget.widget_should_expand:
                container.pack_start(child_widget, expand=True, fill=True)
            else:
                container.pack_start(child_widget, expand=False, fill=True)
            child_widget.show()
            child_widget.parent_widget = parent
            if 'child_widgets' in dir(parent):
                parent.child_widgets.append(child_widget)
            list_of_widgets.append(child_widget)
            return child_widget, size_group

        list_of_widgets = []
        parent_vbox = gtk.VBox()
        size_group = None

        for section in sections:
            if type(section) in (tuple, list):
                title, children = section
                if type(children) is list:
                    child_box = gtk.VBox()
                else:
                    child_box = gtk.HBox()
                frame = vineyard.frame_wrap(child_box, title)
                frame.child_widgets = []
                if type(children) is list:
                    parent_vbox.pack_start(frame, expand=False, fill=False)
                    for child in children:
                        if type(child) is tuple:
                            child_child_box = gtk.HBox()
                            child_child_box.set_homogeneous(True)
                            child_box.pack_start(child_child_box, expand=False, fill=True)
                            for child_child in child:
                                child_widget, size_group = __create_child_and_add_to_container(
                                    child_child,
                                    child_child_box,
                                    frame,
                                    size_group
                                )
                            child_child_box.show()
                        else:
                            child_widget, size_group = __create_child_and_add_to_container(
                                child,
                                child_box,
                                frame,
                                size_group
                            )
                        list_of_widgets.append(child_widget)
                else:
                    parent_vbox.pack_start(frame, expand=False, fill=True)
                    for child in children:
                        child_widget, size_group = __create_child_and_add_to_container(
                            child,
                            child_box,
                            frame,
                            False
                        )
                        list_of_widgets.append(child_widget)
                child_box.show()
                self._evaluate_visibility_from_children(frame, frame.child_widgets)
            else:
                child_widget, size_group = __create_child_and_add_to_container(
                    section,
                    parent_vbox,
                    parent_vbox,
                    size_group
                )
                list_of_widgets.append(child_widget)
        parent_vbox.show()
        return parent_vbox, list_of_widgets

    def _build_notebook_pages(self, pages):
        self.notebook = gtk.Notebook()
        for title, children in pages:
            child_label = gtk.Label(title)
            child_widget, widgets = self._build_frames_with_vbox(children)
            child_widget.set_border_width(6)
            self.notebook.append_page(child_widget, child_label)
            self.widgets.append(widgets)
        self.notebook.show()
        self.notebook.connect_after('switch-page', self._notebook_page_changed)
        return self.notebook

    def __auto_build_interface(self, widgets):
        self._widget = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        self._widget.set_padding(3, 0, 0, 0)
        self.vbox, self.widgets = self._build_frames_with_vbox(widgets)
        self._widget.add(self.vbox)
        self._widget.show()
        self.widget.pack_start(self._widget)

    def __auto_build_pages(self, pages):
        self._widget = self._build_notebook_pages(pages)
        self.widget.pack_start(self._widget)

    """
        Signal handlers
    """

    def _notebook_page_changed(self, notebook, page_gpointer, page_num):
        self.show_page()

    def _child_hide(self, child_widget):
        if 'parent_widget' in dir(child_widget):
            if not len([ i for i in child_widget.parent_widget.child_widgets if i.get_property('visible') ]):
                child_widget.parent_widget.hide()
        else:
            #raise TypeError, "Widget is not contained in a proper frame"
            return True
        return False

    def _child_show(self, child_widget):
        if 'parent_widget' in dir(child_widget):
            child_widget.parent_widget.show()
        else:
            #raise TypeError, "Widget is not contained in a proper frame"
            return True
        return False

    def _loading_settings(self, *args):
        self.gobject.emit('loading-settings', *args[1:])

    def _settings_loaded(self, *args):
        self.gobject.emit('settings-loaded', *args[1:])

    def _settings_changed(self, *args):
        self.gobject.emit('settings-changed', *args[1:])
