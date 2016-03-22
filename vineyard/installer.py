#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import copy, os
import gobject, gtk, wine
from vineyard import common, program_handler, async
from gtkwidgets import icondialog

THREADING = async.ThreadedClass()

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
    ('vcrun2015', 'windows-library', 'MS Visual C++ 2015', _('Microsoft Visual C++ 2015 runtime libraries')),
    ('vcrun2013', 'windows-library', 'MS Visual C++ 2013', _('Microsoft Visual C++ 2013 runtime libraries')),
    ('vcrun2012', 'windows-library', 'MS Visual C++ 2012', _('Microsoft Visual C++ 2012 runtime libraries')),
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

INSTALLERS = INSTALLERS_PROGRAMS + INSTALLERS_EXTRAS


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


def dialog_no_internet(status=None):
    if status is None:
        status = wine.util.get_internet_available()

    #FIXME: Actually show a dialog here


class Winetricks:
    def __init__(self, packages_to_install, parent_window=None, ignore_network=False, callback=None):
        self._DOWNLOADING = False
        self._DOWNLOAD_DIALOG = None
        self._DOWNLOAD_PACKAGES = packages_to_install
        self._INSTALL_ATTEMPT_NR = 1
        self._callback_function = callback
        self.return_status = None

        self.parent_window = parent_window
        if self.parent_window is None:
            self.parent_window = common.get_main_window()

        # Test if the there's internet
        if not ignore_network and not wine.util.get_internet_available():
            dialog_no_internet()
            return

        self._create_dialog()

        # If winetricks is installed, go ahead and install stuff
        if wine.winetricks_installed():
            self._run_winetricks()
        # Else, download winetricks while showing a nice progress dialog
        else:
            self._DOWNLOAD_DIALOG.set_title(_("Downloading winetricks"))
            self._DOWNLOAD_DIALOG.set_markup(_('Downloading winetricks'))
            self._DOWNLOAD_DIALOG.set_markup_second(_('This only needs to be done this once.'))

            self._DOWNLOAD_DIALOG.show_all()

            # Start the download in a new thread and run winetricks when done
            THREADING.run_in_thread(
                wine.update_winetricks,
                callback = self._run_winetricks
            )


    def _run_winetricks(self, return_value=None):
        self._DOWNLOADING = True

        first_package_title = get_installer_from_package_name(
            self._DOWNLOAD_PACKAGES[0]
        )
        if first_package_title is None:
            first_package_title = self._DOWNLOAD_PACKAGES[0]
        else:
            first_package_title = first_package_title['title']

        if len(self._DOWNLOAD_PACKAGES) > 1:
            title = _("Installing {package} and others").format(
                package = first_package_title
            )
        else:
            title = _("Installing {package}").format(
                package = first_package_title
            )

        self._DOWNLOAD_DIALOG.set_title(title)
        self._DOWNLOAD_DIALOG.set_markup(title)
        self._DOWNLOAD_DIALOG.set_markup_second(_(
            "The package files will be cached locally for installation."
        ))

        self._DOWNLOAD_DIALOG.connect('response', self._cancel_winetricks)
        self._DOWNLOAD_DIALOG.show_all()

        # Create the winetricks process
        self._DOWNLOAD_DIALOG.process = self._create_winetricks_process()
        self._DOWNLOAD_DIALOG.process.started_install = False
        # Monitor the winetricks process
        gobject.timeout_add(
            120,
            self._update_installer_dialog
        )


    def _create_dialog(self):
        self._DOWNLOAD_DIALOG = icondialog.IconDialog(
            parent = self.parent_window,
            flags = gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            buttons = (
                (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            ),
            title = _("Installer"),
            image = [
                'system-software-install',
                'system-software-installer',
                'package-x-generic'
            ]
        )

        self._DOWNLOAD_DIALOG.progressbox = gtk.VBox()
        self._DOWNLOAD_DIALOG.vbox.pack_start(self._DOWNLOAD_DIALOG.progressbox, False, True)

        self._DOWNLOAD_DIALOG.progressbar = gtk.ProgressBar()
        self._DOWNLOAD_DIALOG.progressbar.set_pulse_step(0.1)
        self._DOWNLOAD_DIALOG.progressbox.pack_start(self._DOWNLOAD_DIALOG.progressbar, False, True)

        self._DOWNLOAD_DIALOG.button = self._DOWNLOAD_DIALOG.action_area.get_children()[0]


    def _update_installer_dialog(self):
        status = self._DOWNLOAD_DIALOG.process.get_output()
        return_status = None
        if status is None:
            if self._DOWNLOAD_DIALOG.process.started_install:
                self._DOWNLOAD_DIALOG.set_markup_second(_(
                    "Installing package"
                ))
                self._DOWNLOAD_DIALOG.progressbar.set_text(_("Installing..."))
            self._DOWNLOAD_DIALOG.progressbar.pulse()
        else:
            self._DOWNLOAD_DIALOG.process.started_install = True

            if status[0] == 'downloading':
                self._DOWNLOAD_DIALOG.set_markup_second(_(
                    "The package files will be cached locally for installation."
                ))
                self._DOWNLOAD_DIALOG.progressbar.set_text(_("Downloading {file}").format(
                    file = status[1]
                ))
                self._DOWNLOAD_DIALOG.progressbar.set_fraction(
                    float(status[2] / 100.)
                )

            elif status[0] == 'already installed':
                self._DOWNLOAD_DIALOG.set_markup_second('')
                self._DOWNLOAD_DIALOG.progressbar.set_text(
                    _("{package} already installed, skipping").format(
                        package = get_installer_from_package_name(status[1])['title']
                ))
                self._DOWNLOAD_DIALOG.progressbar.set_fraction(1.0)

            elif status[0] == 'extracting':
                self._DOWNLOAD_DIALOG.set_markup_second('')
                self._DOWNLOAD_DIALOG.progressbar.set_text(
                    _("Unpacking installation files")
                )
                self._DOWNLOAD_DIALOG.progressbar.pulse()

            elif status[0] == 'executing':
                self._DOWNLOAD_DIALOG.set_markup_second(_(
                    "If an installer window appears, just accept its default settings."
                ))
                self._DOWNLOAD_DIALOG.progressbar.set_text(
                    _("Running {executable_or_installer}".format(
                        executable_or_installer = os.path.basename(status[1])
                    ))
                )
                self._DOWNLOAD_DIALOG.progressbar.pulse()

            elif status[0] == 'faulty file':
                self._DOWNLOAD_DIALOG.set_markup_second('')
                first_package_title = get_installer_from_package_name(
                    self._DOWNLOAD_PACKAGES[0]
                )['title']
                if self._INSTALL_ATTEMPT_NR == 2:
                    if len(self._DOWNLOAD_PACKAGES) > 1:
                        title = _("Installing {package} and others failed").format(
                            package = first_package_title
                        )
                    else:
                        title = _("Installing {package} failed").format(
                            package = first_package_title
                        )
                    self._DOWNLOAD_DIALOG.set_markup(title)
                    self._DOWNLOAD_DIALOG.set_markup_second(
                        _("{executable_or_installer} can either not be downloaded or is an unsupported version.".format(
                            executable_or_installer = os.path.basename(status[1])
                        ))
                    )
                    return_status = False
                else:
                    if len(self._DOWNLOAD_PACKAGES) > 1:
                        title = _("Retrying installing {package} and others").format(
                            package = first_package_title
                        )
                    else:
                        title = _("Retrying installing {package}").format(
                            package = first_package_title
                        )
                    self._DOWNLOAD_DIALOG.set_markup(title)
                    self._DOWNLOAD_DIALOG.progressbar.set_text(
                        _("Mismatching file already exists, trying again")
                    )
                    os.remove(status[1])
                    self._INSTALL_ATTEMPT_NR += 1
                    self._DOWNLOAD_DIALOG.progressbar.set_fraction(0.0)
                    self._DOWNLOAD_DIALOG.process = self._create_winetricks_process()
                    self._DOWNLOAD_DIALOG.process.started_install = False

            elif status[0] == 'success':
                self._DOWNLOAD_DIALOG.set_markup_second('')
                self._DOWNLOAD_DIALOG.progressbar.set_text(
                    _("{package} successfully installed").format(
                        package = get_installer_from_package_name(status[1])['title']
                ))
                self._DOWNLOAD_DIALOG.progressbar.set_fraction(1.0)
                return_status = True

            elif status[0] == 'done':
                self._DOWNLOAD_DIALOG.set_markup_second(_(
                    "Everything successfully installed"
                ))
                return_status = True

            elif status[0] == 'failed':
                self._DOWNLOAD_DIALOG.progressbar.set_text(
                    _("Installation failed")
                )
                return_status = False


        self._DOWNLOADING = self._DOWNLOAD_DIALOG.process.is_alive()

        if return_status is True:
            self._DOWNLOAD_DIALOG.progressbar.set_text(_("Done."))
            self._DOWNLOAD_DIALOG.progressbar.set_fraction(1.0)
            self._DOWNLOAD_DIALOG.button.set_label('gtk-ok')
            self._DOWNLOAD_DIALOG.button.set_use_stock(True)
            return False
        elif return_status is False:
            self._DOWNLOAD_DIALOG.progressbar.set_fraction(0.0)
            # self._DOWNLOAD_DIALOG.progressbar.hide()
            self._DOWNLOAD_DIALOG.button.set_label('gtk-close')
            self._DOWNLOAD_DIALOG.button.set_use_stock(True)
            return False
        self.return_status = return_status

        return True

    def _create_winetricks_process(self):
        first_package_title = get_installer_from_package_name(
            self._DOWNLOAD_PACKAGES[0]
        )
        if first_package_title is None:
            first_package_title = self._DOWNLOAD_PACKAGES[0]
        else:
            first_package_title = first_package_title['title']

        if len(self._DOWNLOAD_PACKAGES) > 1:
            package_name = _("{first_package} and others").format(
                first_package = first_package_title
            )
        else:
            package_name = first_package_title

        return wine.monitor.Winetricks(
            self._DOWNLOAD_PACKAGES,
            name = _("Installer for {package}").format(
                package = package_name
            )
        )

    def _cancel_winetricks(self, *args, **kwargs):
        if self._DOWNLOADING:
            self._DOWNLOAD_DIALOG.process.kill()
        self._DOWNLOAD_DIALOG.destroy()
        if self._callback_function is not None:
            self._callback_function(self.return_status)

