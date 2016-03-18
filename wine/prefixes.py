#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>
#
#
# PREFIX FORMATS
# ==============
#
# The basic Wine format:
#
# prefix/system.reg
# prefix/user.reg
# prefix/userdef.reg
# prefix/dosdevices/
#
# The unified format has these additions:
#
# prefix/wrapper.cfg            - Shell script declaring environment variables
# prefix/[name of frontend]/    - Frontends may place their files in a named dir
# prefix/xdg/                   - The prefix may have local XDG directories
# prefix/xdg/config/               This is useful for not spamming the main dirs
# prefix/xdg/local/share           with unwanted menu files
#
# Legacy python-wine uses a different layout:
#
# prefix/.wine/system.reg
# prefix/.wine/user.reg
# prefix/.wine/userdef.reg
# prefix/.wine/dosdevices/
# prefix/.local/share
# prefix/.config
# prefix/.icons
#
#
# PREFIX META DATA
# ================
#
# The unified format was created in cooperation with Dan Kegel (winetricks),
# Miro Hrončok (wibom), Alexey S. Malakhov (q4wine) and Vincent Povirk (Wine)
# The spec is available at: http://wiki.winehq.org/BottleSpec
#
# python-wine also supports a few of the extra variables proposed by Alexey:
#  ww_winedllpath
#  ww_wineserver
#
# python-wine adds three extra variables to the spec:
#  ww_xdgconfig  - the path used for XDG_CONFIG_HOME
#  ww_xdgdata    - the path used for XDG_DATA_HOME and prepended to XDG_DATA_DIRS
#  ww_winearch
#
# Also, I think I'm the only one calling it "the unified format", just to know

from __future__ import print_function

import os, sys, time
import common, base, util
# These are used when creating new prefixes
import appearance, shellfolders

PREFIXDIRS = "~/.local/share/wineprefixes:~/.winebottles"


def get_prefix_paths(ignore_missing=True, paths=None):
    """Return a list of the directories to use for prefixes.
    If ignore_missing is True then every defined dir is listed, if not, only
    the the ones that exist are returned."""
    if paths is None:
        paths = os.environ.get('WINEPREFIXES', PREFIXDIRS)
        # Try to protect ourself from a wrongfully set environment variable
        if not len(paths.replace(':','').strip()):
            paths = PREFIXDIRS

    return [
        os.path.normpath(path) for path
        in [
            os.path.expandvars(os.path.expanduser(path)) for path
            in filter(len, paths.split(':'))
        ]
        if not ignore_missing or os.access(path, os.R_OK)
    ]

def is_valid_prefix(prefix_path, accept_legacy=False):
    """
    Return True or False depending on whether prefix_path is a WINEPREFIX.
    If the optional accept_legacy argument is True, a path that contains a proper
    WINEPREFIX as a first level sub-directory will also be considered valid."""

    def _test_path(path):
        if type(path) not in (str, unicode):
            return False

        return all([
            os.path.exists(os.path.join(path, _path)) for _path
            in (
                'dosdevices',
                'system.reg',
                #'userdef.reg',
                'user.reg'
            )
        ])

    if not accept_legacy:
        return _test_path(prefix_path)
    else:
        return (
            _test_path(prefix_path) or
            _test_path(os.path.join(prefix_path, '.wine'))
        )

def get_default_metadata():
    """Return the metadata (environment) as it would optimally be set by the system."""
    def _set(key, value):
        # If os.environ has the key use it's value else use given value
        default[key] = os.environ.get(key, value)
        if default[key] is None:
            del default[key]

    default = {
        'WINEPREFIX': os.path.expanduser('~/.wine'),
        'WINEPREFIXNAME': '',
        'WINEPREFIXTYPE': 'simple'
    }
    _set('WINEDLLPATH', ':'.join(filter(len, [
        '{0}/wine'.format(path) for path
        in os.environ.get('LD_LIBRARY_PATH', '/usr/local/lib:/usr/lib').split(':')
    ])))
    _set('WINELOADER', common.which('wine'))
    _set('WINESERVER', common.which('wineserver'))
    _set('WINE', common.which('wine'))
    _set('WINEARCH', 'win64')
    _set('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    _set('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
    _set('XDG_DATA_DIRS', ':'.join(filter(len, [
        os.path.expanduser('~/.local/share') ] +
        os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':')
    )))
    _set('VINEYARD_DATA', os.path.expanduser('~/.wine/vineyard'))
    return default

def get_metadata(prefix_path=None):
    if prefix_path is None:
        prefix_path = os.path.expanduser('~/.wine')

    # Strip trailing slash
    if prefix_path.endswith('/'):
        prefix_path = prefix_path[:-1]
    # Change prefix_path if it's a legacy prefix
    if (
        not os.path.exists(os.path.join(prefix_path, 'system.reg')) and
        os.path.exists(os.path.join(prefix_path, '.wine'))
    ):
        prefix_path = os.path.join(prefix_path, '.wine')

    info_default = get_default_metadata()
    info = {}
    info['WINEPREFIX'] = prefix_path
    info['WINEPREFIXROOT'] = prefix_path
    info['WINEPREFIXNAME'] = info_default['WINEPREFIXNAME']
    info['WINEPREFIXTYPE'] = info_default['WINEPREFIXTYPE']

    if prefix_path == os.path.expanduser('~/.wine'):
        return info_default

    if not os.access(prefix_path, os.R_OK):
        return None

    path_wrapper = os.path.join(prefix_path, 'wrapper.cfg')
    path_namefile = os.path.join(prefix_path, 'vineyard', 'name')
    path_namefile_legacy = os.path.join(prefix_path, '..', '.name')

    # Unified format
    if os.access(path_wrapper, os.R_OK):
        info['WINEPREFIXTYPE'] = 'unified'
        # Run the wrapper.cfg through a shell and get it's variables
        ## NOTE: If this looks a bit complicated, what we do is list the vars
        ## that we need and use a list construct to create the script in the
        ## next step.
        variables = (
            ('WINEPREFIXNAME', ('ww_name', 'wc_name')),
            ('WINEDLLPATH', ('ww_winedllpath', 'wc_winedllpath', 'WINEDLLPATH')),
            ('WINELOADER', ('ww_wineloader', 'wc_wineloader', 'WINELOADER')),
            ('WINESERVER', ('ww_wineserver', 'wc_wineserver', 'WINESERVER')),
            ('WINE', ('ww_wine', 'wc_wine', 'WINE')),
            ('WINEARCH', ('ww_winearch', 'wc_winearch', 'WINEARCH')),
            ('XDG_CONFIG_HOME', ('ww_xdgconfig', 'wc_xdgconfig')),
            ('XDG_DATA_HOME', ('ww_xdgdata', 'wc_xdgdata'))
        )
        for line in filter(len, common.run([
            'sh', '-c', '. "{wrapper}"; {script}'.format(
                wrapper = path_wrapper,
                script = '; '.join([
                    'echo "{variable}="${{{keys}{closure}'.format(
                        variable = variable,
                        keys = ':-${'.join(keys),
                        closure = '}' * len(keys)
                    )
                    for variable, keys
                    in variables
                ]))
        ], cwd=prefix_path)[0].split('\n')):
            parts = line.strip().split('=')
            if len(parts) < 2:
                continue
            # If this key is a valid one for a prefix, use it
            if parts[0] in info_default.keys():
                var = '='.join(parts[1:])
                # Ignore default values
                if len(var) and var != info_default[parts[0]]:
                    info[parts[0]] = var
        if 'XDG_DATA_HOME' in info.keys():
            info['XDG_DATA_DIRS'] = ':'.join(filter(len, [
                info['XDG_DATA_HOME'] ] +
                os.environ.get('XDG_DATA_DIRS', '').split(':')
            ))

    # Pre-Unified (early python-wine version of unified)
    # This type of prefix will be automatically converted to Unified as only
    # the metadata format is different
    elif os.access(path_namefile, os.R_OK):
        info['WINEPREFIXTYPE'] = 'preunified'
        with open(path_namefile, 'r') as _file:
            info['WINEPREFIXNAME'] = _file.read().strip()

    # Legacy (older version of python-wine)
    elif os.access(path_namefile_legacy, os.R_OK):
        info['WINEPREFIXTYPE'] = 'legacy'
        info['WINEPREFIXROOT'] = os.path.normpath(os.path.join(prefix_path, '..'))
        with open(path_namefile_legacy, 'r') as _file:
            info['WINEPREFIXNAME'] = _file.read().strip()


    # Pre-Unified and Legacy don't define if they have custom XDG dirs
    # so we check for them..
    if info['WINEPREFIXTYPE'] in ('preunified', 'legacy'):
        if os.path.isdir(os.path.join(info['WINEPREFIX'], 'xdg')):
            info['XDG_CONFIG_HOME'] = os.path.join(
                info['WINEPREFIX'], 'xdg/config')
            info['XDG_DATA_HOME'] = os.path.join(
                info['WINEPREFIX'], 'xdg/local/share')
            info['XDG_DATA_DIRS'] = ':'.join(filter(len, [
                os.path.join(info['WINEPREFIX'], 'xdg/local/share') ] +
                os.environ.get('XDG_DATA_DIRS', '').split(':')
            ))
        elif (
            info['WINEPREFIXTYPE'] == 'legacy' and
            os.path.isdir(os.path.join(info['WINEPREFIX'], '../.local/share'))
        ):
            info['XDG_CONFIG_HOME'] = os.path.normpath(os.path.join(
                info['WINEPREFIX'], '../.config'))
            info['XDG_DATA_HOME'] = os.path.normpath(os.path.join(
                info['WINEPREFIX'], '../.local/share'))
            info['XDG_DATA_DIRS'] = ':'.join(filter(len, [
                os.path.normpath(os.path.join(info['WINEPREFIX'], '../.local/share'))
                ] + os.environ.get('XDG_DATA_DIRS', '').split(':')
            ))

    if info['WINEPREFIXNAME'] == '':
        if info['WINEPREFIXTYPE'] != 'simple':
            print(
                "This prefix is in a weird format, skipping: {0}".format(prefix_path),
                file=sys.stderr
            )
        info['WINEPREFIXNAME'] = os.path.basename(prefix_path)

    info['WINEARCH'] = get_prefix_arch(prefix_path)

    info['VINEYARD_DATA'] = os.path.join(info['WINEPREFIX'], 'vineyard')

    return info

def write_metadata(prefix_path=None, data=None):
    """
    Save metadata to the prefix.
    The prefix used is by default the currently used one, but can be overriden
    by the prefix_path argument.
    The metadata can be specified by the data argument, else it is taken from
    the prefix's running environment."""
    if prefix_path is None:
        try:
            prefix_path = common.ENV.get('WINEPREFIX')
        except:
            raise StandardError, 'No prefix in use (that\'s weird...)'

    is_default_prefix = prefix_path == os.path.expanduser('~/.wine')

    info_default = get_default_metadata()
    info = get_metadata(prefix_path)

    if data is None:
        data = {}

    if info is None:
        raise IOError, "Prefix path does not exist."

    # Save the new type of prefix data no matter the previous type since nothing
    # will be overwritten in any case
    #if info.get('WINEPREFIXTYPE', 'simple') in ('unified', 'preunified', 'simple'):
    content = []
    for key, name in [
        ('WINEPREFIXNAME', 'ww_name'),
        ('WINEDLLPATH', 'ww_winedllpath'),
        ('WINELOADER', 'ww_wineloader'),
        ('WINESERVER', 'ww_wineserver'),
        ('WINE', 'ww_wine'),
        ('XDG_CONFIG_HOME', 'ww_xdgconfig'),
        ('XDG_DATA_HOME', 'ww_xdgdata'),
        ('WINEARCH', 'ww_winearch')
    ]:
        # Get variable, first try given data, then common.ENV, then saved info
        var = data.get(key, common.ENV.get(key, info.get(key, None)))
        # If variable is set
        if var is not None:
            # Don't report WINEPREFIXNAME for default prefix (it's always blank)
            if key == 'WINEPREFIXNAME' and is_default_prefix:
                continue
            # Ignore default variables
            if var == info_default[key]:
                continue
            # Escape shell characters - FIXME: The spec doesn't have this!
            #var = var.replace('\\', '\\\\').replace('$', '\\$').replace('"', '\\"')
            var = util.string_escape_char(var, ('\\', '$', '"'))
            # Replace WINEPREFIX with PWD so the directory can be moved
            var = var.replace(
                util.string_escape_char(prefix_path, ('\\', '$', '"')),
                '$PWD'
            )
            content.append('{0}="{1}"'.format(name, var))

    content = '\n'.join(content)
    with open(os.path.join(prefix_path, 'wrapper.cfg'), 'w') as _file:
        _file.write(content)

    # A preunified format prefix is the same as unified apart from the
    # metadata file, so delete the old metadata file, effectively converting
    # the prefix to unified format.
    if info.get('WINEPREFIXTYPE', 'simple') == 'preunified':
        #disabled for testing
        #os.remove(os.path.join(prefix_path, 'vineyard', 'name'))
        pass

    return content


def iter():
    """
    Iterate the prefixes defined in either the standard prefix path or
    the ones defined in the WINEPREFIXES environment variable.
    This function yields a tuple containing (name, info)
    where name is the name of the prefix (with added numbers in case of duplicates)
    and info is a dict containing the environment the prefix should use."""
    prefix_names = []
    for path in get_prefix_paths():
        for prefix in sorted(os.listdir(path), key=str.lower):
            path_full = os.path.join(path, prefix)
            if not is_valid_prefix(path_full, accept_legacy=True):
                continue
            info = get_metadata(os.path.join(path, prefix))
            name = info['WINEPREFIXNAME']
            name_nr = 0
            while name in prefix_names:
                name = '{0} ({1})'.format(info['WINEPREFIXNAME'], name_nr+1)
                name_nr += 1
            prefix_names.append(name)
            # This value is useful for GUIs in the case of multiple prefixes with same name
            info['WINEPREFIXLISTEDNAME'] = name
            yield (name, info)

def list():
    """
    Returns a dict of the prefixes defined in either the standard prefix path or
    the ones defined in the WINEPREFIXES environment variable.
    The dict's keys are the names of the prefixes (with added numbers in case of duplicates)
    and the values are another dict containing the environment the prefix should use."""
    return dict(iter())


def get_metadata_from_name(name, prefix_dict=None):
    """Get the metadata from the prefix with the given name.
    This will simply go through the dict of prefixes and give the most likely match."""

    if name is None:
        return get_metadata(os.path.expanduser('~/.wine'))

    if prefix_dict is None or type(prefix_dict) is not dict:
        prefix_dict = list()

    listnames = prefix_dict.keys()

    # Try precise matching
    if name in listnames:
        return prefix_dict[name]
    else:
        # Try lowercase matching
        name_lower = name.lower()
        for listname in listnames:
            if name_lower == listname.lower():
                return prefix_dict[listname]
        # Try wildcard matching
        if name.endswith('*'):
            name_wildcard = name.split('*')[0].lower()
            for listname in listnames:
                if listname.lower().startswith(name_wildcard):
                    return prefix_dict[listname]
    return None

def get_metadata_from_name_or_prefix(prefix_name_or_path):
    if type(prefix_name_or_path) is str and (
        prefix_name_or_path.startswith('/') and os.path.exists(prefix_name_or_path)
    ):
        prefix_data = get_metadata(prefix_name_or_path)
    else:
        prefix_data = get_metadata_from_name(prefix_name_or_path)
    if prefix_data is None:
        raise StandardError, "Couldn't find prefix"
    return prefix_data



### USE / CREATE(ADD) / REMOVE A PREFIX ###

def use(prefix_name_or_path):
    prefix_data = get_metadata_from_name_or_prefix(prefix_name_or_path)
    data = get_default_metadata()
    data.update(prefix_data)
    common.ENV.update(data)
    if (
        common.ENV['WINEPREFIX'] == os.path.expanduser('~.wine') and
        not os.path.exists(common.ENV['WINEPREFIX'])
    ):
        print("Creating default Wine prefix...")
        wine_first_run()


def remove(prefix_path=None):
    if prefix_path is None:
        prefix_data = get_metadata(common.ENV['WINEPREFIX'])
    else:
        prefix_data = get_metadata(prefix_path)
    path = prefix_data['WINEPREFIX']


    if not os.path.isdir(path):
        error("Bottle doesn't exist.")
        return False

    if prefix_data['WINEPREFIXTYPE'] == 'legacy':
        path = os.path.normpath(os.path.join(path, '..'))

    return common.system(["rm", "-rf", path]) == 0


def add(prefix_name, prefix_path=None):
    if prefix_name is None or not len(prefix_name.strip()):
        raise ValueError, prefix_name
    if prefix_path is None:
        prefix_path = create_dir_name(prefix_name)

    # Make sure the directory the prefix will be in exists
    prefix_basedir = os.path.dirname(prefix_path)
    if not os.path.isdir(prefix_basedir):
        if not os.access(os.path.dirname(prefix_basedir), os.W_OK):
            raise IOError, "Couldn't create prefix base path, you don't have the necessary permissions."
        # Wine will always create a win64 arch prefix if the directory exists
        # https://bugs.winehq.org/show_bug.cgi?id=29661
        # os.mkdir(prefix_basedir)

    # We need to let Wine set up the prefix before we can write to it
    # so set up an environment that matches what we will write when the prefix exists
    prefix_data = {
        'WINEPREFIXNAME': prefix_name,
        'WINEPREFIXTYPE': 'unified',
        'XDG_DATA_HOME': os.path.join(prefix_path, 'xdg', 'local', 'share'),
        'XDG_CONFIG_HOME': os.path.join(prefix_path, 'xdg', 'config')
    }
    data = get_default_metadata()
    data.update(prefix_data)
    data['WINEPREFIX'] = prefix_path
    common.ENV.update(data)

    # Now let Wine set up the prefix
    returncode = wine_first_run()

    # Now create our extra files and folders
    if returncode:
        for path in (
            prefix_path,
            os.path.join(prefix_path, 'xdg'),
            os.path.join(prefix_path, 'xdg', 'local'),
            os.path.join(prefix_path, 'xdg', 'local', 'share'),
            os.path.join(prefix_path, 'xdg', 'config'),
            os.path.join(prefix_path, 'vineyard')
        ):
            if not os.path.exists(path):
                os.mkdir(path)

        write_metadata(prefix_path, prefix_data)

        use(prefix_path)
        return prefix_path
    else:
        return False



### UTILITY/CONVENIENCE FUNCTIONS / API FUNCTIONS ###

def get_name(prefix_path=None):
    if prefix_path is None:
        if (
            os.path.expanduser(common.ENV.get('WINEPREFIX', '~/.wine')) ==
            os.path.expanduser('~/.wine')
        ):
            return None
        else:
            return common.ENV.get('WINEPREFIXNAME', '')
    else:
        prefix_name = get_metadata(prefix_path)['WINEPREFIXNAME']
        if prefix_name is '':
            return None
        else:
            return prefix_name

def get_prefixpath_from_filepath(path):
    """Try to get the name of the configuration this path is in, if any.
    Returns the path to the prefix, None if no was configuration found."""
    found = None
    path_absolute = os.path.abspath(path)
    for prefix_base in get_prefix_paths():
        for prefix in os.listdir(prefix_base):
            prefix = '{0}/{1}'.format(prefix_base, prefix)
            if (
                path == prefix or
                path.startswith('{0}/'.format(prefix))
            ):
                found = prefix
                break
            prefix_absolute = os.path.abspath(prefix)
            if (
                path_absolute == prefix_absolute or
                path_absolute.startswith('{0}/'.format(prefix_absolute))
            ):
                found = prefix
    if found is not None:
        return found
    return None


def create_dir_name(name=None):
    """Returns the full path to where a prefix with the given name
    would be created."""
    if name is None:
        name = util.string_random(length=8)
    else:
        # Make name safe for use on any filesystem (use only alphanumeric chars)
        name = util.string_safe_chars(name, remove_repeats=True).lower()

    prefix_dirname = name[:]
    prefix_basedir = get_prefix_paths(ignore_missing=False)[0]

    prefix_path = os.path.join(prefix_basedir, prefix_dirname)
    # If the desired prefix directory name already exists, come up with a new
    if os.path.exists(prefix_path):
        nr = 1
        while os.path.exists(prefix_path):
            prefix_path = os.path.join(
                prefix_basedir,
                '{name}-{nr}'.format(
                    name = name,
                    nr = nr
                )
            )
            nr += 1

    return prefix_path


def get_prefix_root(prefix_path=None):
    """
    Return the root of the prefix. In most cases this is the same as WINEPREFIX,
    but not for Legacy prefixes where it is the directory above."""
    if prefix_path is None:
        prefix_path = common.ENV['WINEPREFIX']
    if prefix_path == os.path.expanduser('~/.wine'):
        return prefix_path
    elif (
        os.path.normpath(os.path.join(prefix_path, '../.wine')) ==
        os.path.normpath(prefix_path)
    ):
        return os.path.normpath(os.path.join(prefix_path, '../'))
    elif os.path.exists(prefix_path):
        return prefix_path
    else:
        raise IOError, "prefix_path doesn't exist"


def get_prefix_arch(prefix_path):
    if prefix_path is None:
        prefix_path = common.ENV['WINEPREFIX']

    if os.path.exists("%s/dosdevices/c:/windows/syswow64" % prefix_path):
        return 'win64'
    else:
        return 'win32'



### SHORTCUT FUNCTIONS ###

def set_name(name, prefix_path=None):
    if prefix_path == common.ENV['WINEPREFIX']:
        common.ENV['WINEPREFIXNAME'] = name
    write_metadata(prefix_path, {'WINEPREFIXNAME': name})



### PREFIX SYSTEM FUNCTIONS ###

def wine_first_run():
    # Create Wine structure
    returncode = common.system(
        ['wineboot', '-i'],
        env=common.ENV_NO_DISPLAY()
    )

    # The init process isn't always actually finished when it says it is, so check it first
    checks = 1
    while base.check_setup() is False and checks < 500:
        time.sleep(0.2)
        checks += 1
    if base.check_setup():
        appearance.set_menu_style(True)
        shellfolders.setdefaults()
        return True
    else:
        return False
    #return returncode

def reboot():
    return common.system(
        ['wineboot', '--restart'],
        env=common.ENV_NO_DISPLAY()
    ) == 0

def shutdown():
    return common.system(
        ['wineboot', '--shutdown'],
        env=common.ENV_NO_DISPLAY()
    ) == 0

def end_session(force=False):
    command = ['wineboot', '--end-session']
    if force:
        command.append('--force')
    return common.system(command, env=common.ENV_NO_DISPLAY()) == 0

def kill():
    return common.system(
        ['wineboot', '--kill'],
        env=common.ENV_NO_DISPLAY()
    ) == 0

