#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import page
from vineyard.widgets import (
    tool_registry_editor,
    tool_control_panel,
    tool_command_prompt,
    tool_reboot,
    tool_shutdown,
    tool_programs_end,
    tool_programs_kill,
    tool_open_main_drive,
    tool_open_terminal,
    tool_lowercase_files,
    tool_run_executable
)

id = 'tools'
position = 1.0

class Page(page.VineyardPage):
    def __init__(self, dev=False):
        self.no_loading = True
        page.VineyardPage.__init__(self,
            name = _("Tools"),
            icon = 'applications-accessories',
            widgets = [
                (_('Windows accessories'), [
                    tool_registry_editor,
                    tool_control_panel,
                    tool_command_prompt
                ]),
                (_('Windows functions'), [(
                    tool_reboot,
                    tool_shutdown
                ),(
                    tool_programs_end,
                    tool_programs_kill
                )]),
                (_('Configuration functions'), [
                    tool_open_main_drive,
                    tool_open_terminal,
                    tool_lowercase_files,
                    tool_run_executable
                ])
            ])
