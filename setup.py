#!/usr/bin/env python

import os, sys
from distutils.core import setup

script_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
with open('%s/debian/changelog' % script_dir, 'r') as file_obj:
    lines = file_obj.readlines()
    deb_version = lines[0].split('(')[1].split(')')[0]

if 'TRAVIS' in os.environ && 'CI' in os.environ:
  etc_dir = '../etc'
  deb_version = os.environ['TRAVIS_TAG']
else:
  etc_dir = '/etc'


setup( name = "vineyard",
       version = deb_version,
       description = "Easy to use Wine configuration program",
       maintainer = "Christian Dannie Storgaard",
       maintainer_email = "cybolic@gmail.com",
       url = "https://launchpad.net/vineyard",
       license = "LGPL-2",
       scripts = ['vineyard-preferences', 'vineyard-cli', 'vineyard-launcher', 'vineyard-indicator'],
       packages = ['wine', 'vineyard', 'vineyard.pages', 'vineyard.widgets', 'vineyard.gtkwidgets'],
       data_files = [
           ('share/vineyard', [
               'data/vineyard-preferences.glade',
           ]),
           ('share/vineyard/bin', [
               'data/bin/%s' % i for i
               in os.listdir('%s/data/bin' % script_dir)
           ]),
           ('share/vineyard/docs', [
               'data/docs/%s' % i for i
               in os.listdir('%s/data/docs' % script_dir)
           ]),
           ('share/man/man1', [
               'data/vineyard-preferences.1.gz'
           ]),
           ('%s/xdg/autostart' % etc_dir, [
               'data/vineyard-indicator.desktop'
           ]),
           ('lib/nautilus/extensions-2.0/python', [
               'data/%s' % i for i
               in os.listdir('%s/data' % script_dir)
               if 'nautilus' in i and i.endswith('.py')
           ]),
           ('share/applications', [
               'data/vineyard-preferences.desktop',
               'data/vineyard-launcher.desktop'
           ]),
           ('share/vineyard/icons', [
               'data/icons/%s' % i for i
               in os.listdir('%s/data/icons' % script_dir)
               if i.split('.')[-1].lower() in ('svg', 'png')
           ]),
           ('share/icons/hicolor/16x16/apps', [
               'data/icons/16/regedit.png',
               'data/icons/16/taskmgr.png',
               'data/icons/16/wcmd.png'
           ]),
           ('share/icons/hicolor/22x22/apps', [
               'data/icons/22/vineyard-preferences.svg',
               'data/icons/22/regedit.png',
               'data/icons/22/taskmgr.png',
               'data/icons/22/wcmd.svg'
           ]),
           ('share/icons/hicolor/32x32/apps', [
               'data/icons/32/vineyard-preferences.svg',
               'data/icons/32/regedit.png',
               'data/icons/32/taskmgr.png',
               'data/icons/32/wcmd.svg'
           ]),
           ('share/icons/hicolor/48x48/apps', [
               'data/icons/48/vineyard-preferences.svg',
               'data/icons/48/vineyard.svg',
               'data/icons/48/regedit.png',
               'data/icons/48/taskmgr.png',
               'data/icons/48/wcmd.svg'
           ]),
           ('share/icons/Faenza/apps/scalable', [
               'data/icons/Faenza/scalable/vineyard.svg',
               'data/icons/Faenza/scalable/vineyard-preferences.svg'
           ]),
           ('share/icons/Faenza/status/22', [
               'data/icons/Faenza/status/22/vineyard-panel-alert.svg',
               'data/icons/Faenza/status/22/vineyard-panel-idle.svg'
           ]),
           ('share/icons/Faenza-Dark/status/22', [
               'data/icons/Faenza-Dark/status/22/vineyard-panel-alert.svg',
               'data/icons/Faenza-Dark/status/22/vineyard-panel-idle.svg'
           ]),
           ('share/icons/Humanity/status/22', [
               'data/icons/Humanity/status/22/vineyard-panel-alert.svg',
               'data/icons/Humanity/status/22/vineyard-panel-idle.svg'
           ]),
           ('share/icons/ubuntu-mono-dark/status/22', [
               'data/icons/ubuntu-mono-dark/status/22/vineyard-panel-alert.svg',
               'data/icons/ubuntu-mono-dark/status/22/vineyard-panel-idle.svg'
           ]),
           ('share/icons/ubuntu-mono-light/status/22', [
               'data/icons/ubuntu-mono-light/status/22/vineyard-panel-alert.svg',
               'data/icons/ubuntu-mono-light/status/22/vineyard-panel-idle.svg'
           ]),
       ] + [
           (
               'share/vineyard/locale/%s/LC_MESSAGES' % l,
               [
                   'data/locale/%s/LC_MESSAGES/%s' % (l, f) for f
                   in os.listdir('%s/data/locale/%s/LC_MESSAGES' % (script_dir, l))
                   if f.lower().endswith('.mo')
               ]
            ) for l
           in os.listdir('%s/data/locale' % script_dir)
       ]
)
