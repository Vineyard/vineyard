#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
import page
from vineyard.widgets import drives
from vineyard.widgets import folder_desktop, folder_documents, folder_pictures, folder_music, folder_videos

id = 'places'
position = 0.2

class Page(page.VineyardPage):
    def __init__(self, dev=False):
        page.VineyardPage.__init__(self,
            name = _("Places"),
            icon = 'folder',
            pages = [
                (_('Drives'), [
                    drives
                ]),
                (_('Folders'), [
                    folder_desktop,
                    folder_documents,
                    folder_pictures,
                    folder_music,
                    folder_videos
                ])
            ])
