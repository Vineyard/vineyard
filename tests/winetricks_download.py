#!/usr/bin/python

import gtk
from vineyard import installer

try:
    os.remove(os.expanduser('~/.winetrickscache/Xvid-1.2.2-07062009.exe'))
    os.remove(os.expanduser('~/.winetrickscache/divx-7/DivXInstaller.exe'))
except:
    pass

installer.Winetricks(['xvid', 'divx'])
gtk.main()