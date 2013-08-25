#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import registry, common, util

_openargs = []

GNOME_A11Y_DEFAULT_STATE = None

def get(program=None):
	if program:
		program = program.lower()
		# Does this program use a virtual desktop?
		desktop = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\Explorer' % program.lower(), "Desktop", quiet=True)
		if desktop:
			desktop = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Explorer\\Desktops', desktop, quiet=True)
			if desktop:
				return tuple([ int(i) for i in desktop.lower().split('x') ])
			else:
				return None
	else:
		# Does the default configuration use a virtual desktop?
		desktop = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Explorer', "Desktop", quiet=True)
		if desktop:
			desktop = util.string_remove_escapes(desktop)
			desktop = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Explorer\\Desktops', desktop, quiet=True)
			if desktop:
				return tuple([ int(i) for i in desktop.lower().split('x') ])
			else:
				return None

def set(boolean, size=None, program=None):
	"""
		Set whether Wine should emulate a virtual desktop

		@param boolean whether the virtual desktop should be used
		@type  boolean
		@param size    the size of the the virtual desktop in pixels
		@type  tuple   (width,height) - defaults to 800x600 (like winecfg)
		@param program if set, the virtual desktop should only be set for this program
		@type  string  "explorer.exe"

	"""
	if program is not None:
		program = program.lower()

	if common.ENV['VINEYARDCONFNAME'] == '':
		conf_name = 'Default'
	else:
		conf_name = common.ENV['VINEYARDCONFNAME']

	print("Size:", size)
	if size is None:
		if program:
			size = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Explorer\\Desktops', program, quiet=True)
		else:
			size = registry.get(
		        'HKEY_CURRENT_USER\\Software\\Wine\\Explorer\\Desktops',
		        conf_name, quiet=True)
			if not size:
				size = registry.get(
			    'HKEY_CURRENT_USER\\Software\\Wine\\Explorer\\Desktops',
			    'Desktops', quiet=True)
		if not size:
			size = (800, 600)
		else:
			size = tuple([ int(i) for i in size.split('x') ])
	else:
		size = tuple(size)

	print("Set desktop {0} as {1}".format(conf_name, size))
	if boolean:
		if program:
			registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Explorer\\Desktops': {
			    program: '%sx%s' % size}})
			registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\Explorer' % program : {
			    "Desktop": program}})
		else:
			registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Explorer\\Desktops': {
			    conf_name: '%sx%s' % size}})
			registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Explorer': {
			    "Desktop": conf_name}})
	else:
		if program:
			registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\Explorer' % program : {
			    "Desktop": None}})
		else:
			registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Explorer': {
			    "Desktop": None}})

def set_open(name, size):
	_openargs.append("explorer")
	_openargs.append("/desktop=%s,%s" % ('-'.join(name.split(' ')), size.lower()))

def get_repeat_key():
	return common.value_as_bool(common.run([
	    'gconftool',
	    '--get', '/desktop/gnome/peripherals/keyboard/repeat'
	])[0])

def set_repeat_key(state):
	global GNOME_A11Y_DEFAULT_STATE
	# If this is the first time (in this session) that we touch this value
	# get its default
	if GNOME_A11Y_DEFAULT_STATE is None:
		GNOME_A11Y_DEFAULT_STATE = common.value_as_bool(common.run([
		    'gconftool',
		    '--get', '/apps/gnome_settings_daemon/plugins/a11y-keyboard/active'
		])[0])

	state = common.value_as_bool(state)
	# Only enable/disable a11y if it was previously enabled
	if GNOME_A11Y_DEFAULT_STATE:
		common.run([
			'gconftool',
			'--set', '/apps/gnome_settings_daemon/plugins/a11y-keyboard/active',
			'--type', 'bool',
			str(state).lower()
		])
	common.run([
	    'gconftool',
	    '--set', '/desktop/gnome/peripherals/keyboard/repeat',
	    '--type', 'bool',
	    str(state).lower()
	])
	return state
