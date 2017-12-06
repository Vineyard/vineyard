#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import gobject, gtk, pango, sys, re, wine
try:
    import dbus
except ImportError:
    dbus = None
from vineyard import common, async

THREADING = async.ThreadedClass()

class MonitoredProgram:
    def __init__(self, command, name, disable_pulseaudio = False):

        if disable_pulseaudio:
            wine.common.run('killall pulseaudio', shell=True)
        self._disable_pulseaudio = disable_pulseaudio

        self.process = wine.run(
            command,
            name = name
        )

        self.name = name
        self.wine_index = self.process.child.log_filename_base
        self._dialog_already_shown = False

        print("Process started. PID = {0}, PGRP = {1}".format(
            self.process.pid,
            wine.util.get_pgid_of_pid(self.process.pid)
        ))
        gobject.timeout_add(500, self._start_monitoring)
        # And run it now in case the program dies before the first 500 ms
        self._start_monitoring()

    def _start_monitoring(self):
        #print "Checking if program lives.."
        if self.process.is_alive() or len(self.process.get_children()):
            #print "It does. Do nothing"
            #print "Running just fine...", self.process.child.returncode
            return True
        else:
            #print "It's dead Jim!"
            if (
                self._disable_pulseaudio and
                not wine.util.get_pid_from_process_name('pulseaudio')
            ):
                # Wait for any child processes of the program to end first
                # (e.g. so we don't start PulseAudio when a launcher starts a game)

                self.process.wait_for_children()

                # Check if PulseAudio still isn't running and start it if not
                if not wine.util.get_pid_from_process_name('pulseaudio'):
                    print("All children exited. Restarting PulseAudio")
                    wine.common.Popen(
                        'pulseaudio',
                        stdin = 'null', stdout = 'null', stderr = 'null'
                    )

            if not _indicator_lives() and not self._dialog_already_shown:
                #print "Indicator is not alive, show error"
                self._dialog_already_shown = True
                stderr = self.process.read_stderr()
                missing_dlls = self.process.explain_missing_dlls()
                if len(stderr):
                    show_program_error_question(
                        name = self.name,
                        stderr = stderr,
                        missingdlls = missing_dlls
                    )
            #else:
                #print "Indicator is alive, do nothing"
            return False

def _indicator_lives():
    if dbus != None:
        ## FIXME: Why does this have to be so complex?
        ##        There has to be an easier method...
        try:
            applications = dbus.SessionBus().get_object(
                'org.ayatana.indicator.application',
                '/org/ayatana/indicator/application/service'
            ).get_dbus_method('GetApplications')()

            for application in applications:
                for info in application:
                    if str(info).startswith('/org/ayatana/NotificationItem/vineyard'):
                        return True
            return False
        except dbus.exceptions.DBusException:
            return False
    else:
        return False

class show_program_error_question:
    def __init__(self, name, stderr, missingdlls):
        self.name = name
        self.errors = {
            'stderr': stderr,
            'missing-dlls': missingdlls
        }
        self._show_dialog_program_error_question()

    @async.mainloop_method
    def _show_dialog_program_error_question(self, offer_info=True):
        dialog = gtk.MessageDialog(parent=common.get_main_window(),
                                   flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                   type=gtk.MESSAGE_ERROR,
                                   buttons=gtk.BUTTONS_OK)
        dialog.set_icon_name('vineyard-preferences')
        dialog.set_markup('<span weight="bold" size="larger">%s</span>' % \
            _("The program exited with an error"))
        if self.name == 'winetricks':
            dialog.format_secondary_markup(unicode('The installation program did ' + \
                'not exit cleanly. You may have success with simply running it again.'))
        else:
            dialog.format_secondary_markup(unicode('The program <b>%(program)s</b> did ' + \
                'not exit cleanly and any work or progress you may have ' + \
                'done in the program may have been lost.') % \
                {'program': common.escape_xml(self.name)})
        settings = gtk.settings_get_default()
        settings.set_property('gtk-alternative-button-order', True)
        if offer_info:
            button_info = gtk.Button(_("More info"))
            dialog.add_action_widget(button_info, 10)
            dialog.set_alternative_button_order([10, gtk.RESPONSE_OK])
        dialog.set_default_response(gtk.RESPONSE_OK)
        dialog.connect("response", self._on_dialog_main_response)
        dialog.show_all()

    def _on_dialog_main_response(self, dialog, response):
        dialog.destroy()
        error_text = self.errors['stderr']
        missing_dlls = self.errors['missing-dlls']
        if response == 10:
            show_explanation = False

            text = _("A possible cause of the error could be one or more of the following:")+"\n"

            for dll in missing_dlls.keys():
                text += "\n\t"+_("The library file (DLL) <b>%s</b> wasn't found.") % dll

            missing_packages = []
            for packages in missing_dlls.values():
                for package in packages:
                    if package not in missing_packages:
                        missing_packages.append(package)

            if len(missing_packages):
                if len(missing_packages) == 1:
                    text += str("\n\n"+_(
                        "Based on this output it looks like " +
                        "you need to install <b>{package}</b> in order " +
                        "to get <b>{program}</b> to run successfully."
                    )).format(
                        package = missing_packages[0],
                        program = common.escape_xml(self.name)
                    )
                else:
                    list_of_packages = (
                        _("{comma_separated_list} and {last_part}").format(
                            comma_separated_list = _(", ").join(
                                [
                                    "<b>{0}</b>".format(i)
                                    for i in missing_packages[:-1]
                                ]
                            ),
                            last_part = missing_packages[-1]
                    ))
                    text += str("\n\n"+_(
                        "Based on this output it looks like " +
                        "you need to install {packages} in order to get " +
                        "<b>{program}</b> to run successfully."
                    )).format(
                        packages = list_of_packages,
                        program = common.escape_xml(self.name)
                    )
                show_explanation = True
            # We didn't find anything, just display the raw output
            else:
                text = _(
                    "When running <b>{program_name}</b> " +
                    "Wine returned the following errors:"
                ).format(program_name = common.escape_xml(self.name))

            self._show_dialog_program_error(self.name,
                text,
                error_text,
                show_explanation)
        else:
            sys.stdout.write(error_text+'\n')

    def _show_dialog_program_error(self, program_name, text, error, show_explanation=False):
        self._error_dialog = gtk.Dialog(_("Error information for %s") % program_name,
            parent = common.get_main_window(),
            flags = gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_NO_SEPARATOR,
            buttons = (gtk.STOCK_OK, gtk.RESPONSE_OK))

        hbox = gtk.HBox(spacing=6)

        icon = gtk.Image()
        icon.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG)
        icon.set_alignment(0.5, 0.0)

        hbox.pack_start(icon, expand=False, fill=True)

        vbox = gtk.VBox()

        label = gtk.Label()
        label.set_line_wrap(True)
        label.set_alignment(0.0, 0.5)
        label.set_markup('%s' % text)
        label.set_size_request(
            common.widget_get_char_width(label)*80,
            -1
        )

        vbox.pack_start(label, expand=False, fill=True)

        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledwindow.set_size_request(
            common.widget_get_char_width(scrolledwindow)*80,
            common.widget_get_char_height(scrolledwindow)*6)

        textview = gtk.TextView()
        textview.get_buffer().set_text(error)
        textview.modify_font(pango.FontDescription('monospace'))
        textview.set_cursor_visible(False)
        scrolledwindow.add(textview)

        if not show_explanation:
            vbox.pack_start(scrolledwindow, expand=True, fill=True)
        else:
            expander = gtk.Expander(_("Detailed error information"))
            expander.add(scrolledwindow)
            vbox.pack_start(expander, expand=True, fill=True)

        hbox.pack_start(vbox, expand=True, fill=True)

        self._error_dialog.vbox.pack_start(hbox, expand=True, fill=True)

        self._error_dialog.connect('destroy', self._on_dialog_program_error_response)
        self._error_dialog.connect('response', self._on_dialog_program_error_response)

        self._error_dialog.show_all()

    def _on_dialog_program_error_response(self, *args):
        self._error_dialog.destroy()
