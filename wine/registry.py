#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

from __future__ import print_function

import os, sys, re, codecs
import util, parsers, common

import subprocess

import logging as _logging

logging = _logging.getLogger("python-wine.registry")
debug = logging.debug
error = logging.error

def get_codepage():
    filename = __get_branch_file('HKEY_LOCAL_MACHINE')[0]
    branch = 'System\\CurrentControlSet\\Control\\Nls\\CodePage'
    try:
        with open(filename, 'r') as _file:
            codepage = _file.read().lower().split(
                util.string_escape_char(branch.lower(), '\\')
            )[1].split('"acp"="')[1].split('"')[0]
        return 'cp{0}'.format(codepage)
    except (IOError, IndexError):
        # Windows default
        return 'cp1252'

def __get_branch_file(branch):
    if branch.lower().startswith('hkey_local_machine\\system\\mounteddevices'):
        return None, None

    if (
        branch.startswith('HKEY_LOCAL_MACHINE') and
        os.path.exists('%s/system.reg' % common.ENV['WINEPREFIX'])
    ):
        return ('%s/system.reg' % common.ENV['WINEPREFIX'], 'HKEY_LOCAL_MACHINE')

    elif (
        branch.startswith('HKEY_CURRENT_USER') and
        os.path.exists('%s/user.reg' % common.ENV['WINEPREFIX'])
    ):
        return ('%s/user.reg' % common.ENV['WINEPREFIX'], 'HKEY_CURRENT_USER')

    elif (
        branch.startswith('HKEY_CURRENT_USER') and
        os.path.exists('%s/user.reg' % common.ENV['WINEPREFIX'])
    ):
        return ('%s/user.reg' % common.ENV['WINEPREFIX'], 'HKEY_CURRENT_USER')

    elif (
        branch.startswith('HKEY_USERS\\.Default') and
        os.path.exists('%s/userdef.reg' % common.ENV['WINEPREFIX'])
    ):
        return ('%s/userdef.reg' % common.ENV['WINEPREFIX'], 'HKEY_USERS\\.Default')
    else:
        return None, None

def __branch_to_dict(branch, dict):
    parents = []
    for path in filter(len, branch.split('\\')):
        pathname = 'dict%s' % ''.join([ '[\'%s\']' % i for i in parents ])
        if path not in eval(pathname) or type(eval(pathname)) != type({}):
            exec('%s[\'%s\'] = {}' % (pathname, path))
        parents.append(path)
    return dict

def __set_branch_values(branch, dict, items):
    # Make sure the dict keys exist
    dict = __branch_to_dict(branch, dict)
    # Set the value
    pathname = 'dict%s' % ''.join([ '[\'%s\']' % i for i in filter(len, branch.split('\\')) ])
    for key, value in items.iteritems():
        try:
            exec ('{path}[\'{key}\'] = value'.format(
                path = pathname,
                key = util.string_escape_char(key, ['\\', "'"])
            ))
        except ValueError:
            error("Error in registry! Pathname: %s\tKey: %s\tValue: %s" % (pathname, key, value))
    return dict

def _writeRegistry(registrycontent):
    _initWine()
    regfilename = util.tempname('setregistry-', '.reg')
    with codecs.open(regfilename, 'w', encoding=get_codepage()) as regfile:
        regfile.write(registrycontent)
    #print("Running regedit with no display output")
    process = common.Popen(
        [common.ENV['WINE'], "regedit", regfilename],
        stdout = 'null', stderr = 'null',
        env = common.ENV_NO_DISPLAY(common.ENV_NO_GECKO())
    )
    process.communicate()
    return process.returncode
    #returnvalue = subprocess.call(["regedit", regfilename], env=common.ENV_NO_DISPLAY)
    #os.remove(regfilename)
    #return returnvalue

def __get_branch(branch=None, quiet=True, only_use_regedit=False):
    if only_use_regedit == False:
        debug("Using cache/file to read registry.")
        branch_file_name, branch_root = __get_branch_file(branch)
        if branch_file_name != None:
            with codecs.open(branch_file_name, 'r', encoding=get_codepage()) as registry_file:
                registry = registry_file.read()
                #CACHE[branch_root] = registry
                return (branch_root, registry)

    debug("Using regedit to read registry.")
    _initWine()
    process_args = [common.ENV['WINE'], "regedit", "/E", "-"]
    if branch != None:
        process_args.append(branch)
    else:
        branch = ''
    registry = ''
    process = common.Popen(
        process_args,
        env = common.ENV_NO_DISPLAY(common.ENV_NO_GECKO())
    )
    buffer = process.stdout.readline()
    while buffer != '':
        registry += buffer
        buffer = process.stdout.readline()
    #if process.returncode and not quiet:
    if registry == '' or registry.strip() == 'Success':
        if not quiet:
            error("Warning: Registry branch '%s' doesn't exist." % branch)
        return ''
    try:
        registry = registry.decode(get_codepage())
    except UnicodeDecodeError:
        pass
    return registry

def __get_shallow_branch_from_file(branch, filename=None, findkey=None):
    if filename == None:
        filename, branch_root = __get_branch_file(branch)
        if filename == None:
            return None
    else:
        branch_root = branch.split('\\')[0]
    debug("REGISTRY: Reading from file \"{0}\"".format(filename))

    with codecs.open(filename, 'r', encoding = get_codepage()) as file_obj:
        sections = parsers.parse_registry_to_sections(file_obj.read())
    #print("REGISTRY: Registry contains the following branches:"+ \
    #    '\n\t'.join([ key for key, value in sections ])
    #)

    # Remove branch_root from branch to get its relative path/name
    branch_name = branch_root.join(branch.split(branch_root+'\\')[1:])
    # Remove any surplus of backslashes
    branch_name = re.sub(r'\\+', r'\\', branch_name)
    # Convert one bachslashes to two to match the way reg-files are written
    branch_name = branch_name.lower().replace('\\', '\\\\')

    branch_name_parts = filter(len, branch_name.split('\\'))
    branch = {} # Failsafe, the root will most likely be defined again below

    sorted_sections_starting_with_branch_name = sorted(
        (
            (key.lower(), value)
            for key, value
            in sections
            if key.lower().startswith(branch_name)
        ), key=lambda (key, value): len(key)
    )
    _subsections_in_first_level_of_branch = [
        filter(len, key.split('\\'))[-1].lower()
        for key, value in sorted_sections_starting_with_branch_name
        if len(filter(len, key.split('\\'))) == len(branch_name_parts)+1
    ]
    #print("REGISTRY: Registry branches that start with what you're looking for:"+\
    #    '\n\t'.join([ key for key, value in sorted_sections_starting_with_branch_name ])
    #)
    for section_name, section in sorted_sections_starting_with_branch_name:
        section_name_parts = filter(len, section_name.split('\\'))

        if section_name_parts == branch_name_parts:
            branch = parsers.parse_registry_section_to_dict(section)
        else:
            sub_section_name = section_name_parts[len(branch_name_parts):]
            if findkey is None:
                if len(sub_section_name) > 1:
                    debug("REGISTRY: Full branch requested.\n\tFindkey is {0}\n\tBranch name is {1}".format(findkey, sub_section_name)
                    )
                    # This is a sub-sub-branch:
                    # The full branch is requested and this function doesn't
                    # deal with sub-sub-sections, let the full parser do that
                    return None
                else:
                    # This branch is in level 1, add it to the branch
                    branch[sub_section_name[0]] = (
                        parsers.parse_registry_section_to_dict(section)
                    )
            else:
                sub_section_name = sub_section_name[0]
                if sub_section_name.lower() == findkey.lower():
                    # This is a sub-section, specifically the one that was requested
                    # Return a tuple containing which branch (name)
                    # we returned and the sub-branch
                    return (sub_section_name, parsers.parse_registry_section_to_dict(section))
                else:
                    # This is a sub-section, but a findkey was given so it is
                    # not needed, just continue
                    continue
    return branch
    #section = [ i[1] for i in sections if i[0].lower() == branch_name ]
    #if len(section):
    #    section = section[0]
    #else:
    #    return None

    #return parsers.parse_registry_section_to_dict(section)

def __branchpath_in_dict(dict, branch):
    try:
        __get_dict_from_branchpath(dict, branch)
        return True
    except:
        return False

def __get_dict_from_branchpath(dict, branch):
    try:
        return eval('dict%s' % ''.join([ '[\'%s\']' % i for i in filter(len, branch.split('\\'))]))
    except NameError:
        return False

def __set_dict_from_branchpath(dict, branch, value):
    exec('dict%s = value' % ''.join([ '[\'%s\']' % i for i in filter(len, branch.split('\\'))]))
    return dict

def get(branch=None, findkey=None, quiet=True, shallow=False, only_use_regedit=True):
    if shallow:
        reg = __get_shallow_branch_from_file(branch, findkey=findkey)
        if reg != None:
            if findkey:
                if type(reg) is tuple and reg[0].lower() == findkey.lower():
                    return reg[1]
                elif findkey in reg:
                    return reg[findkey]
                else:
                    return None
            else:
                return reg
        else:
            debug("Couldn't get shallow branch for \"%s\", returning deep branch." % (
                branch
            ))

    if findkey:
        fullbranch = '%s\\%s' % (branch, findkey)
    else:
        fullbranch = branch

    branch_output = __get_branch(branch, only_use_regedit = only_use_regedit)
    if type(branch_output) == tuple:
        reg = parsers.parseRegistry(branch_output[1], branch_output[0], encoding=get_codepage())
    else:
        reg = parsers.parseRegistry(branch_output, encoding=get_codepage())

    if reg == None:
        reg = {}
    else:
        try:
            reg = __get_dict_from_branchpath(reg, branch)
        except KeyError:
            if findkey:
                return None
            else:
                return {}

    if findkey:
        if findkey in reg:
            retvalue = reg[findkey]
        else:
            reg_keys_lowercase = [ i.lower() for i in reg.keys() ]
            if findkey.lower() in reg_keys_lowercase:
                retvalue = reg.get(
                    reg.keys()[reg_keys_lowercase.index(findkey.lower())]
                )
            else:
                retvalue = None
    else:
        retvalue = reg

    return retvalue

def set(branches):
    """
    Set registry values.
    Branches should be a dict similar to:
    {
     'HKEY_CURRENT_USER\\Software\\Wine':
      {"Version": "winnt"},
    'HKEY_CURRENT_USER\\Control Panel\\Desktop':
      {"FontSmoothing": "2"}
    }"""
    registry = u'REGEDIT4\n'

    definedbranches = []
    for b in sorted(branches.keys()):
        branchwalk = b.split('\\')
        for i in range(len(branchwalk)-1):
            branch = u'\n[%s\\%s]\n' % (branchwalk[0], '\\'.join(branchwalk[1:i+2]))
            if branch not in definedbranches:
                registry += branch
                definedbranches.append(branch)
        # Add the values
        for key,value in sorted(branches[b].iteritems()):
            key = key.replace('\\', '\\\\').replace('"', '\\"')
            if type(value) is int:
                value = str(value)
            elif type(value) in (str, unicode):
                value = util.string_escape_char(
                    util.string_escape_char(value, '\\').replace('\\', '\\\\'),
                    '"'
                )
            if value == '-' or value == None:
                registry += u'"{key}"=-\n'.format(
                    key = key.decode('utf-8')
                )
            elif str(value).startswith('hex:') or str(value).startswith('dword:'):
                registry += u'"{key}"={value}\n'.format(
                    key = key.decode('utf-8'),
                    value = value
                )
            else:
                try:
                    registry += u'"{key}"="{value}"\n'.format(
                        key = key.replace('"', '\\"').decode('utf-8'),
                        value = value.decode('utf-8')
                    )
                except TypeError:
                    print(u"Error in creating .reg file.\n"+ \
                        u"\tKey: {0}\n\tValue: {1}".format(
                            key, value
                        ),
                    file=sys.stderr)
    registry += u'\n'
    _writeRegistry(registry)

def set_from_file(filename):
    try:
        with codecs.open(filename, 'r', encoding = get_codepage()) as registry_file:
            registry = registry_file.read()

        _writeRegistry(registry)

    except IOError:
        error("Couldn't read registry file \"%s\"" % filename)
        return False

def _initWine():
    _wineprocess = common.Popen(
        "%s -p10" % common.ENV['WINESERVER'],
        shell = True,
        stdin = 'null',
        stdout = 'null',
        stderr = 'null',
        env = common.ENV_NO_DISPLAY(common.ENV_NO_GECKO())
    )

