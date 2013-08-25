#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import copy, os
import gobject, gtk, widget, wine
from vineyard import common, installer

INSTALLERS_PROGRAMS = [
    ('7zip', '7zip', "7-Zip", _('A file archiver with a high compression ratio')),
    ('adobeair', 'adobeair', "Adobe Air", _('An application platform')),
    ('ie6', 'ie', 'Internet Explorer 6', _('Microsoft Internet Explorer 6')),
    ('ie7', 'ie', 'Internet Explorer 7', _('Microsoft Internet Explorer 7')),
    ('mpc', 'mpc', 'Media Player Classic', _('A free audio and video player for Windows')),
    ('shockwave', 'shockwave', 'Shockwave Player', _('Adobe Shockwave Player')),
    ('quicktime72', 'quicktime', 'Quicktime 7.2', _('Apple Quicktime')),
    ('steam', 'steam', 'Steam', _('Steam Client from Valve')),
    ('vlc', 'vlc', 'VLC', _('VLC media player')),
    ('wmp9', 'wmp', 'Windows Media Player 9', _('Microsoft Windows Media Player 9 *')),
    ('wmp10', 'wmp', 'Windows Media Player 10', _('Microsoft Windows Media Player 10 *'))
]

# FIXME: This should be automaticallu matched against what the currently
#        installed version of winetricks can actually do.
INSTALLERS_EXTRAS = [
    ('d3dx9', 'directx', 'Direct3D', _("Direct3D from DirectX 9")),
    ('flash', 'flash', 'Adobe Flash', _('Adobe Flash Player ActiveX and Firefox plugins')),
    ('divx', 'package-x-generic', 'DivX', _('DivX video codec')),
    ('xvid', 'package-x-generic', 'Xvid', _('Xvid video codec')),
    ('gdiplus', 'windows-library', 'GDI+', _('Microsoft Windows GDI+ library')),
    ('mfc40', 'windows-library', 'Microsoft Foundation Classes', _('MFC module from Microsoft Visual C++')),
    ('dotnet11', 'windows-library', '.NET 1.1', _('Microsoft .NET *')),
    ('dotnet20', 'windows-library', '.NET 2.0', _('Microsoft .NET 2.0 *')),
    ('dotnet20sp2', 'windows-library', '.NET 2.0 SP2', _('Microsoft .NET 2.0 Service Pack 2 *')),
    ('dotnet30', 'windows-library', '.NET 3.0', _('Microsoft .NET 3.0*')),
    ('vb6run', 'windows-library', 'MS Visual Basic 6', _('Microsoft Visual Basic 6 Service Pack 6 runtime')),
    ('vb5run', 'windows-library', 'MS Visual Basic 5', _('Microsoft Visual Basic 5 runtime')),
    ('vb4run', 'windows-library', 'MS Visual Basic 4', _('Microsoft Visual Basic 4 runtime')),
    ('vb3run', 'windows-library', 'MS Visual Basic 3', _('Microsoft Visual Basic 3 runtime')),
    ('vb2run', 'windows-library', 'MS Visual Basic 2', _('Microsoft Visual Basic 2 runtime')),
#    ('mono20', 'mono', 'Mono 2.0', _('Open source .NET implementation')),
#    ('mono22', 'mono', 'Mono 2.2', _('Open source .NET implementation')),
#    ('mono24', 'mono', 'Mono 2.4', _('Open source .NET implementation')),
    ('mono26', 'mono', 'Mono 2.6', _('Open source .NET implementation')),
    ('vcrun2010', 'windows-library', 'MS Visual C++ 2010', _('Microsoft Visual C++ 2010 runtime libraries')),
    ('vcrun2008', 'windows-library', 'MS Visual C++ 2008', _('Microsoft Visual C++ 2008 runtime libraries')),
    ('vcrun2005', 'windows-library', 'MS Visual C++ 2005', _('Microsoft Visual C++ 2005 runtime libraries')),
    ('vcrun2003', 'windows-library', 'MS Visual C++ 2003', _('Microsoft Visual C++ 2003 runtime libraries')),
    ('vcrun6', 'windows-library', 'MS Visual C++ 6', _('Microsoft Visual C++ 2003 libraries')),
    ('msxml3', 'windows-library', 'MS XML 3', _('Microsoft XML Version 3')),
    ('msxml4', 'windows-library', 'MS XML 4', _('Microsoft XML Version 4')),
    ('msxml6', 'windows-library', 'MS XML 6', _('Microsoft XML Version 6')),
    ('ogg', 'package-x-generic', 'Ogg Filters/Codecs', _('flac, theora, speex, vorbix, schroedinger')),
    ('physx', 'package-x-generic', 'NVIDIA PhysX', _('NVIDIA/AEGIAs physics library')),
    ('corefonts', 'gtk-select-font', 'Base Windows Fonts', _('Microsofts Arial, Courier and Times')),
    ('liberation', 'gtk-select-font', 'Liberation Fonts', _('Liberation fonts from Red Hat')),
    ('tahoma', 'gtk-select-font', 'Tahoma Font', _('Microsofts Tahoma'))
]

INSTALLERS = (INSTALLERS_PROGRAMS + INSTALLERS_EXTRAS)

def get_installer_from_package_name(package_name):
    for name, icon, title, description in INSTALLERS:
        if name == package_name:
            return {
                'name': name,
                'icon': icon,
                'title': title,
                'description': description
            }
    return None

class Widget(widget.VineyardWidget):
    def __init__(self):
        widget.VineyardWidget.__init__(self)
        self.title = _("Installers")
        self.widget_should_expand = True
        self.installers_programs = INSTALLERS_PROGRAMS
        self.installers_extras = INSTALLERS_EXTRAS
        self._downloading = False
        self._downloading_dialog = None
        self._build_interface()

    def _build_interface(self):
        self.vbox = gtk.VBox()

        self.installers = []
        installers = []
        for n, (title, section) in enumerate((
            (_('Programs'), self.installers_programs),
            (_('Extras'), self.installers_extras)
        )):
            if n == 0:
                installers.append([None, None, '<header first>%s</header>' % title])
            else:
                installers.append([None, None, '<header>%s</header>' % title])
            self.installers.append(('', '', ''))

            for i in section:
                try:
                    if len(i) > 1:
                        icon = common.pixbuf_new_from_string(i[1])
                        if icon == None:
                            icon = common.pixbuf_new_from_string('package-x-generic')
                        installers.append( (i[0], icon, '%s\n<small>%s</small>' % (i[2], i[3])) )
                    else:
                        installers.append( i[0] )
                    self.installers.append(i)
                except IndexError:
                    print i

        self.list = common.list_view_new_icon_and_text(headers=None, ignore_first_column=True, number_of_text_columns=1, text_column=2, use_markup=True, select_multiple=True, items=installers)
        self.vbox.pack_start(self.list)
        self.license_notice_label = gtk.Label(_('* Legally requires that you own a Windows license'))
        self.license_notice_label.set_alignment(1.0, 0.5)
        self.vbox.pack_start(self.license_notice_label, False, True)
        self.hbox_buttons = gtk.HBox()
        self.hbox_buttons.set_spacing(6)
        self.button_install = common.button_new_with_image('gtk-add', label=_("_Install"), use_underline=True)
        self.button_install.set_sensitive(False)
        self.hbox_buttons.pack_start(self.button_install, True, True)
        self.vbox.pack_start(self.hbox_buttons, False, True)

        self.list.connect('changed', self.list_changed)
        self.button_install.connect('clicked', self.button_install_clicked)

        self.frame = common.frame_wrap(self.vbox, self.title)
        self.pack_start(self.frame, True, True)

        self.sizable = []

        self.show_all()
        self.license_notice_label.hide()

    def _gui_set_program_selected(self, state):
        self.button_install.set_sensitive(state)

    def list_changed(self, listwidget, treeview, active_nr, active_text):
        selected = [ self.installers[i][3] for i in self.list.get_active() ]
        if any(( i.strip().endswith('*') for i in selected )):
            self.license_notice_label.show()
        else:
            self.license_notice_label.hide()
        self._gui_set_program_selected(active_nr != None)

    def button_install_clicked(self, button):
        packages = [ self.installers[i][0] for i in self.list.get_active() ]
        installer.Winetricks(packages, parent_window = common.get_main_window())
