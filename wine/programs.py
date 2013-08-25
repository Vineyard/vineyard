#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import registry
import util, common, prefixes, binary, parsers

import subprocess, os, sys, re, difflib, copy, operator, stat

import logging as _logging

logging = _logging.getLogger("python-wine.programs")
debug = _logging.debug
info = _logging.info
error = _logging.error
warning = _logging.warning
critical = _logging.critical

IGNORE_PROGRAMS_CONTAINING = ['unins', 'unvise', 'unwise', 'remove']
DOCUMENT_MATCHERS = [
    'help', 'readme', 'read me', 'documentation', 'what\'s new', ' manual',
    '.pdf', ' website', 'release note', 'visit ', ' support'
]

# Program exe/icon filename overrides in regex format
PROGRAM_OVERRIDES = {
    'Steam': {
        'search': ('displayname', r'(?i)^steam$'),
        'replace': [
            ('path', (
                'get_key',
                'HKEY_LOCAL_MACHINE\\Software\\Valve\\Steam', 'InstallPath'
            )),
            ('programexe', (
                'use_key_replace',
                'path',
                '(.*)',
                r'\1\\Steam.exe'
            )),
            ('programicon', (
                'use_key',
                'programexe'
            ))
        ]
    },
    'Steam App': {
        'search': ('_registrykey', r'(?i)^Steam App \d+'),
        'replace': [
            ('programcommand', (
                'use_key_replace',
                'uninstallstring',
                '(.*?) steam://uninstall/(\d*)',
                r'wine \1 -silent -applaunch \2'
            ))
        ]
    },
    'IE6': {
        'search': ('displayname', r'(?i)^Microsoft Internet Explorer 6'),
        'replace': [
            ('name', "Microsoft Internet Explorer 6"),
            ('description', "Web browser from Microsoft"),
            ('publisher', "Microsoft Corporation"),
            ('programexe', (
                'use_key_replace',
                'uninstallstring',
                r'(?i).*IE6Maintenance ([a-z]):\\.*',
                r'\1:\\Program Files\\Internet Explorer\\iexplore.exe'
            )),
            ('path', (
                'use_key_replace',
                'uninstallstring',
                r'(?i).*IE6Maintenance ([a-z]):\\.*',
                r'\1:\\Program Files\\Internet Explorer\\'
            )),
            ('programicon', (
                'use_key',
                'programexe'
            ))
        ]
    },
    '7-Zip': {
        'search': ('displayname', r'(?i)^7-Zip '),
        'replace': [
            ('name', "7-Zip"),
            ('description', "A file archiver with a high compression ratio"),
            ('programexe', (
                'use_key_replace',
                'uninstallstring',
                r'(?i)[\'"]?(.*?)\\Uninstall.exe',
                r'\1\\7zFM.exe'
            )),
            ('path', (
                'use_key_replace',
                'uninstallstring',
                r'(?i)[\'"]?(.*?)\\Uninstall.exe',
                r'\1\\'
            )),
            ('programicon', (
                'use_key',
                'programexe'
            ))
        ]
    },
    'Fallout 3': {
        'search': ('displayname', '(?i)fallout ?3'),
        'replace': [
            ('name', "Fallout 3"),
            ('description', "A post-nuclear first-person role-playing game"),
            ('publisher', "Bethesda Softworks Inc."),
            ('programexe', (
                'use_key_replace',
                'installlocation',
                r'(?i)(.*)',
                r'\1\\FalloutLauncher.exe'
            )),
            ('icon', (
                'use_key_replace',
                'installlocation',
                r'(.*)',
                r'\1\\FalloutLauncher-MCE.png'
            )),
            ('path', (
                'use_key',
                'installlocation'
            ))
        ]
    }
}

REG_EX_FILE_URL = re.compile(r'(?i).*\.(url)')
#REG_EX_FILE_LNK = re.compile(r'(?i).*\.(lnk)')

def __initialise_programs_from_menu():
    return list_from_menu()
PROGRAMS_FROM_MENU = common.deferreddict(__initialise_programs_from_menu)

def __cache_for_list_from_registry_is_up_to_date():
    return 'programs_from_registry' in CACHE

def list_from_settings(prefix_path=None):
    if prefix_path is None:
        data_path = common.ENV['VINEYARD_DATA']
    else:
        data_path = prefixes.get_metadata(prefix_path)
        if 'VINEYARD_DATA' in data_path:
            data_path = data_path['VINEYARD_DATA']
        else:
            return {}
    print("Data path:", data_path)
    programs = {}
    dir_path = os.path.join(data_path, 'applications')
    if not os.path.exists(dir_path):
        return programs

    for filename in os.listdir(dir_path):
        if not filename.lower().endswith('.desktop'):
            continue
        menu_data = parsers.DesktopFile(os.path.join(dir_path, filename))
        program = {}
        for menu_value, program_value in [
            ('Name', 'name'),
            ('Comment', 'description'),
            ('Icon', 'icon'),
            ('Exec', 'programcommand'),
            ('Terminal', 'programterminal'),
            ('Path', 'installlocation'),
            ('Categories', 'category'),
            ('NoDisplay', 'showinmenu'),
            ('X-Wine-Application-ProgramCommand', 'programcommand'),
            ('X-Wine-Application-ProgramIcon', 'programicon'),
            ('X-Wine-Application-RegistryKey', '_registrykey'),
            ('X-Wine-Application-Uninstall', 'uninstall'),
            ('X-Wine-Application-Version', 'version'),
            ('X-Wine-Application-DisablePulseAudio', 'disablepulseaudio')
        ]:
            if menu_value in menu_data:
                program[program_value] = menu_data[menu_value]

        if 'programcommand' in program:
            if program['programcommand'].startswith('vineyard-cli'):
                program['programcommand'] = util.string_split(
                    program['programcommand']
                )[-1]
            if os.path.isfile(util.wintounix(program['programcommand'])):
                program['exe'] = program['programcommand']

        if 'programterminal' in program:
            program['programterminal'] = common.value_as_bool(
                program['programterminal']
            )

        if 'category' in program:
            if program['category'].endswith(';'):
                program['category'] = program['category'][:-1]

        # We're using the opposite of the the XDG keyword here (NoDisplay)
        program['showinmenu'] = not common.value_as_bool(
            program.get('showinmenu', False)
        )

        program['disablepulseaudio'] = common.value_as_bool(
            program.get('disablepulseaudio', False)
        )

        program['parsed from'] = 'setting'

        if '_registrykey' in program:
            identity = program['_registrykey']
        else:
            identity = '.'.join(filename.split('.')[:-1])

        programs[identity] = program

    return programs

def list_from_registry():
    #if 'programs_from_registry' in CACHE:
    #    debug("Cache is up to date, returning cache.")
    #    return CACHE['programs_from_registry']

    registry_data = registry.get('HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall')
    programs = {}
    for program in registry_data.keys():
        if "VineyardName" in registry_data[program]:
            programname = registry_data[program]["VineyardName"]

        elif "DisplayName" in registry_data[program]:
            programname = registry_data[program]["DisplayName"]
        else:
            debug("Skipping program-entry \"%s\", it doesn't have a name." % program)
            continue

        """ Don't overwrite entries with the same same name"""
        if programname in programs:
            """ If this is a case of a duplicate program because of
                InstallShield uninstall info, only use the "proper" program """
            if program.startswith('InstallShield_'):
                continue
            elif 'InstallShield_{0}'.format(program) in registry_data.keys():
                del programs[programname]
            else:
                programname = "%s (%s)" % (programname, program)

        program_dict = registry_data[program].copy()

        program_dict['_registrykey'] = program
        debug("Adding program \"%s\"" % programname)
        if "UninstallString" in registry_data[program]:
            if (
                type(registry_data[program]["UninstallString"]) in (str, unicode) and
                len(registry_data[program]["UninstallString"])
            ):
                program_dict["UninstallString"] = util.string_remove_quotes(
                    registry_data[program]["UninstallString"].replace('\\"', '"')
                )
            else:
                del program_dict["UninstallString"]

        for key, value in program_dict.items():
            try:
                if value.endswith('\x00'):
                    program_dict[key] = value[:-1]
            except AttributeError:
                # Only strings should be in the dict, so if anything else
                # shows up, nuke it
                del program_dict[key]

        programs[programname] = program_dict

    CACHE['programs_from_registry'] = programs
    return programs

def list_from_menu2():
    # Cache disabled, searching is often faster
    """try:
        nr_files_in_dir, files = CACHE.get('programs-list-of-desktop-files')
        if nr_files_in_dir == util.get_number_of_files_in_dir('{0}/.local/share/applications/'.format(home)):
            return files
    except KeyError:
        pass"""

    wineprefix = common.ENV['WINEPREFIX']
    # Strip any trailing /
    wineprefix = wineprefix[:-1] if wineprefix.endswith('/') else wineprefix
    # Find files containing the WINEPREFIX using a bit of a trick: -Z makes grep print filenames/matches separated by \x00
    # so we can split the result and turn it into a dict and -z makes grep consider lines ended by \x00 instead of \n and
    # thus prints the entire matching "line" meaning the entire file (unless the file is written in non-standard format).
    """output = common.Popen("grep -rzZ '{0}\"' {1}/.local/share/applications/*wine*".format(common.ENV['WINEPREFIX'], common.ENV['HOME']),
        stdout=subprocess.PIPE, shell=True, executable='bash').communicate()[0]
    # Strip any trailing \x00 from the output
    output = output[:-1].split('\x00') if output.endswith('\x00') else output.split('\x00')

    # Convert paired list of <file name>, <file content> to dict and return it
    files = dict(zip(output[::2], output[1::2]))"""

    files = util.find_files_containing_string(
        #'{0}/.local/share/applications/wine'.format(common.ENV['HOME']),
        '{0}/applications/wine'.format(common.ENV['XDG_DATA_HOME']),
        '{0}'.format(common.ENV['WINEPREFIX']),
        endswith = '.desktop',
        return_file_content = True
    )
    files = dict(files)

    #nr_files_in_dir = util.get_number_of_files_in_dir('{0}/.local/share/applications/'.format(common.ENV['HOME']))
    nr_files_in_dir = util.get_number_of_files_in_dir('{0}/applications/'.format(common.ENV['XDG_DATA_HOME']))

    CACHE['programs-list-of-desktop-files'] = (nr_files_in_dir, files)
    return files

def __cache_for_list_from_menu():
    # The cache tests whether a value is up to date against the registry
    # so we need to do our own test here, since we need to test against
    # the menu-items folder.
    # NOTE: This function is not run currently. It is faster not to check.
    if 'programs_from_menu' in CACHE:
        cached_desktop_list, cached_values = CACHE.get('programs_from_menu')
    else:
        cached_desktop_list, cached_values = 0, 0

    debug("Looking through menu entries made by wine...")
    output = common.Popen(['find', '%s/../.local/share/applications/' % common.ENV['WINEPREFIX'],
                           '-iwholename', '*/wine/*.desktop']).communicate()[0]
    desktoplist = filter(len, output.split("\n"))

    if cached_desktop_list == desktoplist:
        debug("Programs from menu entries cache is up to date, returning cache.")
        return True, cached_values
    else:
        return False, desktoplist

def list_from_menu():
    #cache_up_to_date, data = __cache_for_list_from_menu()
    #if cache_up_to_date:
    #    return data
    #else:
    #    desktoplist = data
    #
    #debug("Filtering the found list and adding their info to the list...")
    desktop_programs = {}
    #for path in desktoplist:
    #    desktopfile = open(path).readlines()
    desktop_files = list_from_menu2()
    for path, data in desktop_files.iteritems():
        try:
            name = data.split('Name=')[1].split('\n')[0]
        except IndexError:
            name = ''
            print "Warning: {0} doesn't have a name!".format(path)
        try:
            command = data.split('Exec=')[1].split('\n')[0].replace('\\\\','\\')
        except IndexError:
            command = None
        try:
            icon = data.split('Icon=')[1].split('\n')[0]
        except IndexError:
            icon = None
        try:
            comment = data.split('Comment=')[1].split('\n')[0]
        except IndexError:
            comment = None
        try:
            uninstall = data.split('X-Vineyard-Application-Uninstall=')[1].split('\n')[0]
        except IndexError:
            uninstall = None
        """for line in desktopfile:
            line = line.replace("\n", '')
            if line.startswith("Name="):
                name = '='.join(line.split('=')[1:])
            elif line.startswith("Exec="):
                command = '='.join(line.split('=')[1:]).replace('\\\\','\\')
            elif line.startswith("Icon="):
                icon = '='.join(line.split('=')[1:])
            elif line.startswith("Comment="):
                comment = '='.join(line.split('=')[1:])"""

        #prefix = re.match(r'env WINEPREFIX=["\']?(.*?)["\']? wine', command)
        #if prefix:
        #    if util.wintounix(prefix.groups()[0]) == os.path.normpath(common.ENV['WINEPREFIX']):
        desktop_programs[name.lower()] = {
            'Name': name,
            'Command': command,
            'Icon': icon,
            'Comment': comment,
            'Uninstall': uninstall,
            'Path': os.path.realpath(os.path.dirname(path)),
            'PathFull': path
        }
        #    else:
        #        debug("Skipping menu entry for \"%s\", it doesn't seem to belong to this configuration." % name)

    debug("Done. Returning list of menu entries.")
    CACHE['programs_from_menu'] = (desktop_files.keys(), desktop_programs)
    return desktop_programs

def get(from_registry=True, from_menus=True):
    """if __cache_for_list_from_registry_is_up_to_date():
        debug("Programs from registry cache is up to date...")
        if include_menu_only_entries:
            if __cache_for_list_from_menu()[0]:
                debug("Programs from menu entries cache is up to date...")
                if 'program_listing_including_menu_entries' in CACHE:
                    debug("Returning cached program listing including menu entries.")
                    return CACHE['program_listing_including_menu_entries']
                else:
                    debug("The full program listing isn't cached, rebuilding...")
        elif 'program_listing' in CACHE:
            debug("Returning cached program listing excluding menu entries.")
            return CACHE['program_listing']"""

    programs_from_settings = list_from_settings()

    if from_registry:
        programsFromReg = list_from_registry()
        programsFromMenuRaw = {}
        programsFromMenu = {}
        menuOnlyPrograms = {}
    if from_menus:
        programsFromMenuRaw = list_from_menu()
        # Filter the programsFromMenu dict for items containing names like "Uninstall", "Help", etc.
        programsFromMenu = dict(
            (k, v)
            for (k, v)
            in programsFromMenuRaw.iteritems()
            if len(k) and is_valid_program_name(k)
        )
        # Remove empty values from programsFromMenu's subitems
        programsFromMenu = dict(
            (k, dict(
                (sk, sv)
                for (sk, sv)
                in v.iteritems()
                if sv is not None
            ))
            for (k, v)
            in programsFromMenu.iteritems()

        )
        programs = {}
        menuOnlyPrograms = copy.deepcopy(programsFromMenu)


    for program, program_data in programs_from_settings.iteritems():
        yield program_data

    if from_registry and len(programsFromReg.keys()):
        #reg_version1 = re.compile('(?:(?:\w+) ?)+ \(([\w\d\-\.]*)\)') # This one breaks?
        reg_version1 = re.compile('\s\(?([\w]?\d\-\.]*)\)?')
        reg_version2 = re.compile(' [vV]?\.?((?:\d+\.?)*?)$')

        for regKey,regData in programsFromReg.iteritems():
            # See if we haven't edited this program earlier
            # and just load the saved values if we have
            if regData['_registrykey'] in programs_from_settings.keys():
                debug("Skipping already added: %s" % regData['_registrykey'])
                continue
            print(regKey)

            # Lowercase keys to ensure better matching and emove empty values
            regData = dict(
                (k.lower(), v)
                for (k, v)
                in regData.iteritems()
                if len(v)
            )

            # Don't count programs without names
            if 'vineyardname' not in regData and 'displayname' not in regData:
                continue

            if 'vineyardname' in regData:
                full_name = name = regData['vineyardname']
            else:
                full_name = regData['displayname']
                name = return_valid_program_name(full_name, clean=False)

            program = {
                'name': name,
                '_registrykey': regData['_registrykey']
            }

            for overridename,override in PROGRAM_OVERRIDES.iteritems():
                if 'search' in override:
                    key, search = override['search']
                    if key in regData and re.search(search, regData[key]):
                        debug("Found override \"%s\" for \"%s\"" % (overridename, full_name))
                        for pkey,rvalue in override['replace']:
                            if type(rvalue) == type(()):
                                if rvalue[0] == 'use_key':
                                    if rvalue[1] in regData:
                                        program[pkey] = regData[rvalue[1]]
                                    elif rvalue[1] in program:
                                        program[pkey] = program[rvalue[1]]

                                elif rvalue[0] == 'use_key_replace':
                                    key_value = ''
                                    match_key, match_value, replace_value = rvalue[1:]
                                    if match_key in regData:
                                        key_value = regData[match_key]
                                    elif match_key in program:
                                        key_value = program[match_key]
                                    debug("Checking the override rule \"%s\" matches \"%s\"" % (match_value, key_value))
                                    match_value_matchobj = re.search(match_value, key_value)
                                    if match_value_matchobj:
                                        debug("Rule matches, applying override logic to key \"%s\"" % pkey)
                                        program[pkey] = match_value_matchobj.expand(replace_value)

                                elif rvalue[0] == 'get_key':
                                    key_value = registry.get(rvalue[1], rvalue[2])
                                    if key_value is not None:
                                        program[pkey] = key_value

                                elif rvalue[0] == 'get_key_replace':
                                    _root, _key, _search, _replace = rvalue[1:]
                                    key_value = registry.get(rvalue[1], rvalue[2])
                                    if key_value is not None:
                                        program[pkey] = key_value
                                        debug("Checking the override rule \"%s\" matches \"%s\"" % (_search, key_value))
                                        _match_obj = re.search(_search, key_value)
                                        if _match_obj:
                                            debug("Rule matches, applying override logic to key \"%s\"" % pkey)
                                            program[pkey] = _match_obj.expand(_replace)

                            else:
                                program[pkey] = rvalue
                            if pkey in ['path', 'programexe', 'programicon', 'icon'] and pkey in program:
                                program[pkey] = util.wintounix(program[pkey])

            # Copy data from registry info
            if 'vineyardname' in regData:
                program['name'] = regData['vineyardname']
            if 'vineyardicon' in regData:
                program['icon'] = get_icon({'name': program['name'], 'icon': regData['vineyardicon']})
            if 'vineyardcommand' in regData:
                program['programcommand'] = regData['vineyardcommand']
            if 'vineyarddescription' in regData:
                program['description'] = regData['vineyarddescription']
            if 'vineyardterminal' in regData:
                program['programterminal'] = common.value_as_bool(
                    regData['vineyardterminal']
                )
            if 'vineyarduninstall' in regData:
                program['uninstall'] = regData['vineyarduninstall']

            if 'displayversion' in regData:
                program['version'] = regData['displayversion']
            else:
                #match = re.search('(?:(?:\w+) ?)+ \(([\w\d\-\.]*)\)', full_name)
                match = reg_version1.search(full_name)
                if match:
                    program['version'] = match.groups()[0]
                else:
                    #match = re.search(' [vV]?\.?((?:\d+\.?)*?)$', full_name)
                    match = reg_version2.search(full_name)
                    if match:
                        program['version'] = match.groups()[0]
            if 'publisher' in regData:
                program['publisher'] = regData['publisher']
            if 'uninstallstring' in regData:
                program['uninstall'] = regData['uninstallstring']

            # Find icon from registry info and possibly executable
            if 'icon' not in program and 'displayicon' not in program and 'programicon' not in program:
                if 'displayicon' in regData:
                    if regData['displayicon'].lower().split(',')[0].endswith('.exe'):
                        program['programicon'] = util.wintounix(regData['displayicon'].split(',')[0])
                        if 'programexe' not in program and is_valid_program_name(program['programicon']):
                            program['programexe'] = util.wintounix(regData['displayicon'].split(',')[0])
                    else:
                        program['icon'] = util.wintounix(regData['displayicon'].split(',')[0])

            # Try to find the directory for the executable
            # We'll look for executable and icon files here
            if 'path' not in program:
                debug("Finding path for program...")
                if 'path' in regData:
                    program['path'] = util.wintounix(regData['path'])
                elif 'basepath' in regData:
                    program['path'] = util.wintounix(regData['basepath'])
                elif 'installlocation' in regData:
                    program['path'] = util.wintounix(regData['installlocation'])
                elif 'uninstallstring' in regData:
                    # Don't use if uninstallstring doesn't contain an absolute path and only use the first executable, not its args
                    matches = [ match for match in re.findall(r'(?i)[\'"]?(\w\:\\.*?\.[a-z_]{3,4})[\'"]? ?', regData['uninstallstring']) if not match.lower().endswith('.dll') ]
                    if len(matches):
                        debug("Converting uninstall string to usable program path...")
                        matches = [ match for match in [ re.sub(r'(?i)(?<=\\)(%s).*?\.(log|txt|lst|exe)' % '|'.join(IGNORE_PROGRAMS_CONTAINING), 'fake_file_name_so_dirname_works', i) for i in matches ] ]
                        if len(matches):
                            debug("Found uninstallstring matches \"%s\" for the program path for \"%s\"" % (matches, program['name']))
                            match = matches[0]
                            #program['path'] = '/'.join(util.wintounix(match.replace('\\fake_file_name_so_dirname_works', '')).split('/')[:-1])
                            program['path'] = '/'.join(util.wintounix(match).split('/')[:-1])
                            # If the innermost dir in the path is called something like "uninstall", use its parent
                            if not is_valid_program_name( program['path'].split('/')[-1] ):
                                program['path'] = '/'.join(program['path'].split('/')[:-1])

            # Search through the install directory for a possible executable and icon if either isn't found yet
            possible_exes = []
            if not (
                'icon' in program or
                'programicon' in program
            ) or 'programexe' not in program:
                debug("Program so far: %s" % program)
                debug("Searching for executables and icons...")
                if 'path' in program and os.path.isdir(program['path']):
                    paths = [program['path']]
                    for filename in os.listdir(program['path']):
                        debug("\tChecking file in path (%s): %s..." % (program['path'], filename))
                        if filename.lower() == "bin":
                            debug("\t\tAdding dir \"%s/%s\" to exe search dir." % (program['path'], filename))
                            paths.append("%s/%s" % (program['path'], filename))
                    for path in paths:
                        for filename in filter(is_valid_program_name, os.listdir(path)):
                            debug("\tChecking if \"%s\" is an executable or an icon..." % filename)
                            if 'icon' not in program and 'programicon' not in program and filename.lower().split('.')[-1] in ['.ico', '.png', '.icon']:
                                icon = "%s/%s" % (path, filename)
                            if filename.lower().endswith('.exe'):
                                debug("\t\tExecutable \"%s\" found, adding to list." % filename)
                                possible_exes.append("%s/%s" % (path, filename))
                debug("Executables found: %s" % possible_exes)
            # Look for an executable in the list of executables in the program's path we just compiled
            if 'programcommand' not in program and 'programexe' not in program and len(possible_exes):
                possible_exe = difflib.get_close_matches(program['name'], possible_exes, 3, 0.0)
                if len(possible_exe):
                    program['programexe'] = possible_exe[0]

            # Try to find a matching menu entry
            menuMatch, menuOnlyPrograms = _find_program_in_menu_that_matches_program_data(program, menuOnlyPrograms, programsFromMenuRaw)

            # Copy usable values from the menuMatch into the program dict
            # though only if this registry value hasn't been touched by Vineyard
            if menuMatch and (
                len([
                    i for i in regData.keys()
                    if i.startswith('vineyard')
                ]) == 0
            ):
                debug("Copying values from the found menu item...")
                # Lowercase all keys in menuMatch to ensure better matching
                menuData = util.dict_to_case_insensitive(menuMatch)
                if 'icon' not in program and 'icon' in menuData:
                    program['icon'] = menuData['icon']
                if 'description' not in regData and 'comment' in menuData:
                    program['description'] = menuData['comment']
                if (
                    'programexe' not in regData and
                    'programcommand' not in regData
                ) and 'command' in menuData:
                    if menuData['command'].startswith('env WINEPREFIX=') or menuData['command'].startswith('wine '):
                        executable = isolate_executable_from_command(menuData['command'])
                        executable = util.wintounix(executable)
                        if is_valid_program_name(executable):
                            program['programcommand'] = menuData['command']
                            program['programexe'] = executable
                    else:
                        program['programexe'] = menuData['command']
                if 'uninstall' in menuData:
                    program['uninstall'] = menuData['uninstall']

            if 'programexe' in program:
                program['exe'] = program['programexe']
            elif 'programcommand' in program:
                program['exe'] = isolate_executable_from_command(program['programcommand'])

            program['parsed from'] = 'registry'
            yield program
            debug("Program added: %s" % program)

    # Now it's time to find those programs that only recide in the menu
    if from_menus:
        menuprograms = {}
        for menuKey,menuData in menuOnlyPrograms.iteritems():
            # See if we haven't edited this program earlier
            # and just load the saved values if we have
            if menuKey in programs_from_settings:
                debug("Skipping already added: %s" % program)
                continue

            menuData = util.dict_to_case_insensitive(menuData)
            registryKey = "vineyard-program-from-menu-%s" % util.tempstring()
            list_of_used_registrykeys = [ i['_registrykey'] for i in menuprograms.itervalues() ]
            while registryKey in list_of_used_registrykeys:
                registryKey = "vineyard-program-from-menu-%s" % util.tempstring()
            program = {'_registrykey': registryKey}
            program['name'] = menuData['name']
            if 'command' in menuData and menuData['command']:
                if menuData['command'].startswith('env WINEPREFIX=') or menuData['command'].startswith('wine '):
                    executable = isolate_executable_from_command(menuData['command'])
                    executable = util.wintounix(executable)
                    if is_valid_program_name(executable):
                        program['programcommand'] = menuData['command']
                        program['programexe'] = program['exe'] = executable
                        test_var = menuData['command']
                        if executable.lower().endswith('.lnk'):
                            lnk_file = util.wintounix(executable)
                            print("Trying", lnk_file)
                            if os.access(lnk_file, os.R_OK):
                                lnk_file = binary.windows_link(lnk_file)
                                if 'location' in lnk_file:
                                    test_var = lnk_file['location']
                        if REG_EX_FILE_URL.search(test_var):
                            program['is_url'] = True

            if 'icon' in menuData and menuData['icon']:
                program['icon'] = menuData['icon']
            if 'comment' in menuData and menuData['comment']:
                program['description'] = menuData['comment']
            if 'uninstall' in menuData and menuData['uninstall']:
                program['uninstall'] = menuData['uninstall']

            program['parsed from'] = 'menu'
            program['menu file'] = menuData['pathfull']
            #menuprograms[unicode(menuData['name'], errors = 'ignore')] = program

            yield program
            debug("Program (from menu) added: %s" % program)

        CACHE['program_listing_including_menu_entries'] = (programs, menuprograms)
        #return (programs, menuprograms)
    else:
        CACHE['program_listing'] = programs
        #return programs

def _find_program_in_menu_that_matches_program_data(program_data, menu_only_programs = {}, menu_programs = {}):
    debug("Looking for a menu item matching \"%s\"" % program_data['name'])

    """ Remove items containing names like "Uninstall", "Help", etc. """
    programs_from_menu = dict((k, v) for (k, v) in menu_programs.iteritems() if is_valid_program_name(k))
    """ Remove empty values from programs_from_menu's subitems """
    programs_from_menu = dict((k, dict((sk, sv) for (sk, sv) in v.iteritems() if sv is not None)) for (k, v) in programs_from_menu.iteritems())

    if 'programexe' in program_data:
        program_exe = util.wintounix(program_data['programexe'])
    else:
        program_exe = None

    """ Dict of programs in menu, indexed by their executable """
    menu_programs = dict([ (util.wintounix(v['command']), k) for (k, v) in programs_from_menu.iteritems() if 'programexe' in v ])
    debug("%s" % menu_programs)

    menu_item_key = None
    """ First try to match by executable """
    if program_exe in menu_programs.keys():
        menu_item_key = menu_programs[program_exe].replace('\\\\','\\')
        debug("Found menu entry for \"%s\" by executable matching to \"%s\"." % \
            (program_data['name'], menu_item_key))

    """ Go through each of our program name variations and try to match a menu item name """
    if menu_item_key == None:
        """ Variations of the program name """
        program_name_lowercase = program_data['name'].lower()
        # basic means without any version information or "*uninstall*"/"*remove*" parentheses
        program_name_basic = return_valid_program_name(program_data['name'])
        program_name_basic_first_word = return_valid_program_name(program_data['name'].split(' ')[0])

        """ Variations of the names of the programs in the menu """
        menu_names_basic = dict([ (return_valid_program_name(k), k) for k in programs_from_menu.keys() ])
        menu_names_sorted_by_length = sorted(programs_from_menu.keys(), cmp = lambda a,b: len(a)-len(b))

        debug("%s, %s, %s" % (program_name_lowercase, program_name_basic, program_name_basic_first_word))
        debug("%s" % programs_from_menu.keys())
        for try_name in (program_name_lowercase, program_name_basic, program_name_basic_first_word):
            if try_name in programs_from_menu.keys():
                menu_item_key = try_name
                debug("Found menu entry for \"%s\" by lowercase matching to \"%s\"." % \
                    (program_data['name'], menu_item_key))
                break
            elif try_name in menu_names_basic.keys():
                menu_item_key = menu_names_basic[try_name]
                debug("Found menu entry for \"%s\" by basic matching to \"%s\"." % \
                    (program_data['name'], menu_item_key))
                break

    """ If we didn't find a match, try matching to something like "[word] program name [word] version.number" """
    if menu_item_key == None:
        """ Regex matching
            basic program name (possibly preceded or followed by another word) with a version number afterwards """
        regex_name_with_version = re.compile('(?i)(%s( \w*?)?|(\w*? )?%s)[\- ](v|version)?\.?[0-9\.\-]*' % \
            (re.escape(program_name_basic_first_word), re.escape(program_name_basic_first_word)))

        for menu_name in menu_names_sorted_by_length:
            # Match program name to menu name with a version number (see above)
            if regex_name_with_version.match(menu_name):
                menu_item_key = menu_name
                debug("Found menu entry for \"%s\" by regex matching to \"%s\"." % \
                    (program_data['name'], menu_item_key))
                break

    """ If we still didn't find a match, try matching to the first part of the menu name (removing any leading "play") """
    if menu_item_key == None:
        for menu_name in menu_names_sorted_by_length:
            try:
                if menu_name.startswith(program_name_basic_first_word) or \
                   re.sub("^play ", '', menu_name).startswith(program_name_basic_first_word):
                    menu_item_key = menu_name
                    debug("Found menu entry for \"%s\" by start matching to \"%s\"." % \
                        (program_data['name'], menu_item_key))
                    break
            except UnicodeDecodeError:
                error("Error in menu file name:", menu_name)

    """ Done looking for a match in the menu files.
        Remove the match (if any found) from the list of menu-only menu entries
        and return (the_menu_match, the_filtered_menu_list) or None """
    if menu_item_key != None:
        try:
            del menu_only_programs[menu_item_key]
        except KeyError:
            """ This program was already found.
                This is probably a second install of the same program.
                (How should we actually handle this? Right now it usually
                 means that the second install won't be able to use the
                 icon and description from the menu file, but it's still
                 better than the no support that's the default in
                 Windows and Wine) """
            pass
        return programs_from_menu[menu_item_key], menu_only_programs
    else:
        return None, menu_only_programs

def get_print():
    programs = list(get())
    if len(programs):
        programs = sorted(programs, key=lambda i: i['name'].lower())
        for index, program in enumerate(programs):
            print "Program:\t%s" % program['name']
            for key in ['Version:', 'Publisher:', 'Uninstall:', 'Description:', 'Icon:\t', 'ProgramIcon:', 'ProgramCommand:', 'ProgramExe:']:
                if key.lower().split(':')[0] in program:
                    print "%s\t%s" % (key, program[key.lower().split(':')[0]])
            if index != len(programs)-1:
                print ""
    else:
        print "No installed programs in registry."

def return_valid_program_name(name, clean=True):
    if not clean:
        # Change Window's simple character replacements with real characters
        name = unicode(name)
        name = re.sub(r'(?i)\(tm\)', u'™', name)
        name = re.sub(r'(?i)\(c\)', u'©', name)
        name = re.sub(r'(?i)\(r\)', u'®', name)
        name = util.string_remove_escapes(name)
    # Remove anything after and including first parenthesis if it includes the word "uninstall"
    # (some programs have stuff like "(uninstall only)" in their name, this strips it)
    name = re.sub(r'(?i) ?\([^\)]*?(uninstall|remove)[^\(]*?\)','', name)
    # Remove any version number at the end of the name
    name = re.sub('(?i)( v\d[\d\.]*?| \d\.(\d\.?)*)$', '', name)
    if clean:
        return name.lower()
    else:
        return name

def is_valid_program_name(name, remove_help=True):
    badwords = IGNORE_PROGRAMS_CONTAINING
    if remove_help:
        badwords += DOCUMENT_MATCHERS
    name = name.lower()
    for badword in badwords:
        if badword in name:
            return False
    return True

def program_names_match(name1, name2):
    name1 = re.sub('(^play |\..{3}$)', '', return_valid_program_name(name1))
    name2 = re.sub('(^play |\..{3}$)', '', return_valid_program_name(name2))
    if name1 == name2 or \
       name1.startswith(name2) or name2.startswith(name1) or \
       name1.endswith(name2) or name2.endswith(name1):
        return True
    return False

def isolate_executable_from_command(command):
    """ Remove C:\Windows\Command\Start.exe from command """
    command = re.sub(r'(?i)"?[a-z]\:\\+windows\\+command\\+start\.exe"? ?(/\w+ )*','', command)
    """ Isolate the first executable in the command """
    #return re.sub(u'(^(env WINEPREFIX=[\'"].*?[\'"] )?wine "|(?<=[^^\n\r])".*$)', '', command).replace('\\\\', '\\')
    command = re.sub(r'^env WINEPREFIX=[\'"].*?[\'"] ', '', command)
    command = re.sub(r'^wine ', '', command)
    command = command.replace('\\ ', ' ')
    first_command_match = re.search(r'(?i)^"([a-z]:\\.*?)"', command)
    if first_command_match:
        command = first_command_match.groups()[0]
    return command

def set_program_data(program_data):
    if 'menu file' in program_data:
        filename = os.path.basename(program_data['menu file']).split('.desktop')[0]
    elif '_registrykey' in program_data:
        filename = program_data['_registrykey']
    else:
        filename = None

    return write_desktop_file(program_data, filename = filename)

def set_program_options(key, name=None, icon=None, command=None, description=None, terminal=None, uninstall=None, menu_file=None):
    if menu_file is not None:
        print("Saving menu file....")
        menu_data = parsers.DesktopFile(menu_file)
        if name is not None:
            menu_data['Name'] = name
        if icon is not None:
            menu_data['Icon'] = icon
        if command is not None:
            menu_data['Exec'] = command
        if description is not None:
            if 'LANG' in common.ENV and len(common.ENV['LANG']):
                language = common.ENV['LANG'].split('.')[0]
                menu_data['Comment[{0}]'.format(language)] = description
            else:
                menu_data['Comment'] = description
        if terminal is not None:
            menu_data['Terminal'] = terminal
        if uninstall is not None:
            menu_data['X-Vineyard-Application-Uninstall'] = uninstall
        menu_data.save()
        print("done")
    else:
        regData = {}
        if name != None:
            name = unicode(name)
            #name = name.replace(u'™', '(tm)')
            #name = name.replace(u'©', '(c)')
            #name = name.replace(u'®', '(r)')
            regData['VineyardName'] = name
        if icon != None:
            regData['VineyardIcon'] = icon
        if command != None:
            regData['VineyardCommand'] = command
        if description != None:
            regData['VineyardDescription'] = description
        if terminal != None:
            regData['VineyardTerminal'] = str(terminal).lower()
        if uninstall != None:
            regData['VineyardUninstall'] = uninstall
        #print "Setting or adding programkey \"%s\": %s" % (key, regData)
        registry.set({
            ('HKEY_LOCAL_MACHINE\\'+
            'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{0}').format(key): (
                regData
            )
        })

def create_desktop_files():
    for programname, programdata in get().iteritems():
        if 'name' not in programdata:
            programdata['name'] = programname
        write_desktop_file(programdata, "/tmp")

def create_desktop_file_content(program, return_program_data = False):
    if type(program) == type({}):
        program_data = program
    else:
        program_list = get()
        try:
            program_data = program_list[program]
        except KeyError:
            try:
                program_data = [ v for k,v in program_list.iteritems() if k.lower() == program.lower() ][0]
            except IndexError:
                error("Couldn't find a program named \"%s\" to create a desktop file for" % program)
                if return_program_data:
                    return None, None
                else:
                    return None

    content = {}
    content['Name'] = program_data['name']
    if 'programterminal' in program_data:
        content['Terminal'] = str(program_data['programterminal']).lower()
    else:
        content['Terminal'] = 'false'
    content['Type'] = 'Application'
    content['StartupNotify'] = 'true'
    content['Icon'] = get_icon(program_data)

    command = None
    if 'programcommand' in program_data:
        command = program_data['programcommand']
    elif 'programexe' in program_data:
        command = program_data['programexe']
    elif 'exe' in program_data:
        command = program_data['exe']

    content['X-Wine-Application-ProgramCommand'] = command

    prefix = common.ENV['WINEPREFIX']
    if prefix is None:
        prefix = ''

    if command is not None:
        if len(prefix):
            use_conf = '--use-conf "{0}" '.format(
                util.string_escape_char(prefix, '"')
            )
        else:
            use_conf = ''

        if program_data.get('disablepulseaudio', False):
            disable_pulse = '--disable-pulseaudio '
        else:
            disable_pulse = ''

        if program_data.get('cpulimit', False):
            if program_data['cpulimit'] is True:
                cpu_limit = '--cpu-limit 1 '
            else:
                cpu_limit = '--cpu-limit {0} '.format(program_data['cpulimit'])
        else:
            cpu_limit = ''


        content['Exec'] = (
            'vineyard-cli {useconf}{disablepulse}{cpulimit}--run "{command}"'.format(
                useconf = use_conf,
                disablepulse = disable_pulse,
                cpulimit = cpu_limit,
                command = util.string_escape_char(
                    command, ('"', '\\')
                )
        ))

        exe = util.wintounix(isolate_executable_from_command(command))
        if not os.path.exists(exe):
            # The command might be (probably is) surrounded by quotes
            exe = util.wintounix(isolate_executable_from_command(command[1:-1]))

        if os.access(exe, os.X_OK):
            # Only add the TryExec argument if we actually parsed the exe right
            # and it's executable, otherwise we'll end up with a dead menu item
            content['TryExec'] = exe
    """
    elif 'programexe' in program_data:
        if os.path.realpath(common.ENV['WINEPREFIX']) == os.path.realpath(util.getRealHome()+"/.wine"):
            content['Exec'] = "wine \"%s\"" % program_data['programexe']
        else:
            #content['Exec'] = "env HOME=\"%s\" WINEPREFIX=\"%s\" wine \"%s\"" % \
            #    (common.ENV['HOME'], common.ENV['WINEPREFIX'], program_data['programexe'])
            content['Exec'] = 'env '+\
                   'XDG_CONFIG_HOME="{XDG_CONFIG_HOME}" '+\
                   'XDG_DATA_HOME="{XDG_DATA_HOME}" '+\
                   'XDG_DATA_DIRS="{XDG_DATA_DIRS}" '+\
                   'WINEPREFIX="{WINEPREFIX}" '+\
                   'wine "{exe}"'.format(
                       WINEPREFIX = common.ENV['WINEPREFIX'],
                       XDG_CONFIG_HOME = common.ENV['XDG_CONFIG_HOME'],
                       XDG_DATA_HOME = common.ENV['XDG_DATA_HOME'],
                       XDG_DATA_DIRS = common.ENV['XDG_DATA_DIRS'],
                       exe = program_data['programexe']
                    )"""


    if 'description' in program_data:
        content['Comment'] = program_data['description']

    if 'installlocation' in program_data:
        content['Path'] = util.wintounix(program_data['installlocation'])

    if 'category' in program_data:
        content['Categories'] ='{0};'.format(program_data['category'])
    else:
        content['Categories'] ='Wine;'

    if 'showinmenu' in program_data:
        content['NoDisplay'] = (not program_data['showinmenu'])

    content['X-Wine-Application'] = 'true'

    if 'uninstall' in program_data:
        content['X-Wine-Application-Uninstall'] = program_data['uninstall']

    if '_registrykey' in program_data:
        content['X-Wine-Application-RegistryKey'] = program_data['_registrykey']

    if 'programicon' in program_data:
        content['X-Wine-Application-ProgramIcon'] = program_data['programicon']

    if 'version' in program_data:
        content['X-Wine-Application-Version'] = program_data['version']

    content['X-Wine-Application-DisablePulseAudio'] = program_data.get('disablepulseaudio', False)

    content['X-Wine-Application-Prefix'] = prefix

    desktop_content = '#!/usr/bin/env xdg-open\n[Desktop Entry]\n'
    for key in sorted(content.keys()):
        if type(content[key]) in (str, unicode):
            key_content = util.string_escape_char(content[key], '\\').replace('\\', '\\\\')
        else:
            key_content = content[key]

        desktop_content = '{0}{1}={2}\n'.format(
            desktop_content, key, key_content
        )

    if return_program_data:
        return desktop_content, program_data
    else:
        return desktop_content

def write_desktop_file(program, filedir=None, filename=None):
    desktop_content, program = create_desktop_file_content(
        program,
        return_program_data = True
    )

    if desktop_content is None:
        return False

    program_name_simple = str(re.sub('[^\w,.\-+\(\)=\ ]', '?', program['name'].lower()))

    if filedir is None:
        #filedir = os.path.realpath(os.path.expanduser("~/.local/share/applications/"))
        filedir = '{0}/applications/'.format(common.ENV['VINEYARD_DATA'])
        prefix_name = prefixes.get_name()
        if prefix_name is None:
            prefix_name = 'default'
        else:
            util.string_safe_chars(prefix_name, extra_safe_chars=' ')
        menu_path = os.path.expanduser('~/.local/share/applications/vineyard')
        symlink_path = os.path.join(
            menu_path,
            prefix_name
        )
        if not os.path.exists(symlink_path):
            if not os.path.isdir(menu_path):
                if subprocess.call(['mkdir', '--parent', menu_path]) != 0:
                    error("Error: Couldn't create \"%s\"" % menu_path)
                    return False

            os.symlink(filedir, symlink_path)

    if not os.path.isdir(filedir):
        if subprocess.call(['mkdir', '--parent', filedir]) != 0:
            error("Error: Couldn't create \"%s\"" % filedir)
            return False

    if filename is None:
        desktopfilename = os.path.join(
            filedir,
            'vineyard-program-{0}.desktop'.format(program_name_simple)
        )
    else:
        desktopfilename = os.path.join(
            filedir,
            '{0}.desktop'.format(filename)
        )

    with open(desktopfilename, 'w') as _file:
        _file.write(desktop_content)
    os.chmod(desktopfilename, os.stat(desktopfilename).st_mode | stat.S_IXUSR)
    return desktopfilename

def get_icon(program=None, executable=None, force_update=False):
    """Return the path to a program's icon.
    Generates a new icon file if it needs to be extracted."""

    if program is None and type(executable) in (str, unicode):
        program = {
            'programexe': executable,
            'name': executable.replace('/', '-')
        }

    if type(program) is not dict:
        program = get()[program]

    try:
        programname = return_valid_program_name(program['name'])
    except KeyError:
        error("Program doesn't have a name: %s" % program)

    icon_path_generated = os.path.realpath(
        "{datapath}/icons/wine-application-icon-{programname}.png".format(
            datapath = common.ENV['VINEYARD_DATA'],
            programname = programname
        )
    )
    if not os.path.isdir(os.path.dirname(icon_path_generated)):
        common.run(['mkdir', '--parent', os.path.dirname(icon_path_generated)])

    #debug("Looking for icon for \"%s\"" % program['name'])
    places_to_look = [
        util.wintounix(program[key])
        for key in [
            'icon',
            'programicon',
            'programexe',
            'exe'
        ]
        if key in program and program[key] is not None
    ]

    for icon_path in places_to_look:
        # as icon path may simply be an icon name, try to get the full path
        icon_path = util.icon_get_path_from_name(icon_path)

        if icon_path is not None and os.path.isfile(icon_path):

            extension = icon_path.lower().split('.')[-1]

            if extension in ('exe', 'dll'):
                icon_size = util.get_file_size(icon_path, 'mib')

                if icon_size > 0 and icon_size <= common.DONT_PARSE_EXECUTABLES_WITH_SIZE_ABOVE_MB:
                    create_icon_from_exe(icon_path, icon_path_generated)
                    return icon_path_generated

            elif extension == 'ico':
                create_png_from_ico(icon_path, icon_path_generated)
                return icon_path_generated

            return icon_path

    return None


def create_png_from_ico(icopath, destination):
    icons = filter(len, common.run(["icotool", "--list", icopath])[0].split('\n'))
    # If the icon file has any icons
    if len(icons):
        # Sort the icons by height and then by bit depth and pick the first (largest width and highest bit depth)
        index = sorted(
            [
                (int(icon.split('--index=')[1].split()[0]),
                 int(icon.split('--height=')[1].split()[0]),
                 int(icon.split('--bit-depth=')[1].split()[0])
                )
                for icon in icons
                if '--index=' in icon and '--height=' in icon and '--bit-depth=' in icon
            ], key=operator.itemgetter(1,2)
        )[-1][0]
        # Extract and convert the best icon (found above)
        # First try with icotool
        icotool_returncode = common.system([
            "icotool", "-x", "--index", str(index),
            icopath, "-o", destination
        ])
        #if icotool_returncode != 0:
        return 0


def create_icon_from_exe(exe, destination):
    if os.path.exists(exe):
        tmpfilename = util.tempname('vineyard-icon-extraction-', '.ico')
        with open(tmpfilename, 'w') as tmpfile:
            # Extract all icons from inputfile
            common.Popen(["wrestool", exe, "--extract", "--type=group_icon"],
                         stdout=tmpfile).wait()
        # If the extraction gave any fruit
        if os.stat(tmpfilename).st_size:
            return create_png_from_ico(tmpfilename, destination)

        with open(tmpfilename, 'w') as tmpfile:
            # Extract all icons from inputfile
            common.Popen(["wrestool", exe, "--extract", "--raw", "--type=version"],
                         stdout=tmpfile).wait()
        # If the extraction gave any fruit
        if os.stat(tmpfilename).st_size:
            return create_png_from_ico(tmpfilename, destination)

        error("Error: Couldn't read icon(s) from file \"%s\"" % exe)
        return False


def uninstall(program=None, uninstall=None):
    if program is None:
        uninstallstring = uninstall
    else:
        programs = list_from_registry()
        try:
            uninstallstring = programs[program]['UninstallString']
        except KeyError:
            return False
    uninstallstring = util.string_split(uninstallstring)
    process = common.Popen(["wine"]+ uninstallstring, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, env=common.ENV)
    return process.wait()

