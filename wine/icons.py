#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>
#
# Test whether an icon is the default XPM icon that Wine gives programs.
# Colour information is specifically not taken into account, only the pixel information.

import os, re

icons = [
    (['application-x-ms-dos-executable', 'application-x-executable'], """"                                                  x x x x x                                     ",
"                                                  x       x x x x                               ",
"                                                x x             x x x                           ",
"                                                x                   x x x                       ",
"                                              x x                       , x                     ",
"                                              x x                         x                     ",
"                                            x x                         x x                     ",
"                                            x x                         x x                     ",
"                                            x x                         x x                     ",
"                                          x x x                       x x x                     ",
"                                          x x x x                     x x                       ",
"                                        x x x x x x x x x x x x x     x x                       ",
"                                        x x x x x x x x x x x x x x x x x                       ",
"                                        x x x x x x x x x x x x x x x x                         ",
"                                        x x x x x x x x x x x x x x x x                         ",
"                                        x x x x x x x x x x x x x x x                           ",
"                                        x x x x x x x x x x x x x x x                           ",
"                                      x x x x x x x x x x x x x x x                             ",
"                                      x  xxxx x x x x x x x x xxxxxx                            ",
"                                      xxx x x x xxx x x x x x xxxxx                             ",
"                                      xxxxx x x xxx x x x x x xx,xx                             ",
"                                      xxxxx x x x x x x x x x xxx                               ",
"                                      xxxxx x x x x x x x x xxx x                               ",
"                                      xxxxx x x x x x x x x xxx                                 ",
"                                      xxxxx x x x x x x xxxxxxx                                 ",
"                                      xxxxx x x x x x x xxxxx                                   ",
"                                      xxxxx x x xxx x xxxxx xx                                  ",
"                                      x xxxxx x xxxxxxxxxxx                                     ",
"                                        xxxxxxxxxxxxxxxxxx                                      ",
"                                        x xxxxxxxxx x x                                         ",
"                                        xxx x x x x                                             ",
"                                        xxx x x                                                 ",
"                                        x x x                                                   ",
"                                        xxx xx                                                  ",
"                                        x x                                                     ",
"                                        x xx                                                    ",
"                                        x x                                                     ",
"                                        x                                                       ",
"                                        xx                                                      ",
"                                      x x                                                       ",
"                  xxxxx             x x x                                                       ",
"                    x x x x x x x x x x x                                                       ",
"                      x x x x x x x x x x                                                       ",
"                        x x xxx x x x x x x                                                     ",
"                              xxx x x x x x x x                                                 ",
"                                  xxx x x x x xxx                                               ",
"                                        x x x x x x                                             ",
"                                                xxxxx                                           ","""[:-1]),
    (['folder-wine', 'folder'], """"        xxxxxxxxxxxxxxxxxxxxxxxx                                ",
"      xxxxxxxxxxxxxxxxxxxxxxxxxxxx                              ",
"    xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx                            ",
"  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx                          ",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx                        ",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx    ",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  ",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  ","""[:-1]),
    (['text-x-generic'], """"              xxxxxxxxxxxxxxxxxxxxxxxxxx                        ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxx                      ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx                    ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx                  ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx                ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx              ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx              ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"              xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ",
"                  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx            ","""[:-1])
]

def convert(iconfile):
    """Test whether an icon is the default XPM icon that Wine gives programs.
    If it is, then return it's mimetype(s) instead."""
    if not os.access(iconfile, os.R_OK):
        return iconfile

    with open(iconfile, 'r') as _file:
        icon = _file.read()

    if 'xpm' in icon[:10].lower():
        icon = re.sub('[^",\s]','x', icon)
        icon = re.sub('(?m)^"\s*?",?$','', icon)
        icon = ','.join(icon.split(',')[:-1]).strip()
        for info in icons:
            if icon.endswith(info[1]):
                return info[0]

    return iconfile
