#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

from __future__ import print_function

import common, util, monitor, desktop, parsers, binary
import os, sys, urllib, re, subprocess

import logging as _logging

logging = _logging.getLogger("python-wine")
debug = logging.debug
error = logging.error

def check_setup():
    """
        Check whether the Wine installation has been created.
        Returns True or False
    """
    paths = [
        # The user profile directory isn't created by Wine until an application
        # actually puts something in there, so don't look for it.
        #"%s/dosdevices/c:/windows/profiles/%s" % (common.ENV['WINEPREFIX'], common.ENV['USER']),
        "%s/dosdevices/c:/windows/system32" % common.ENV['WINEPREFIX'],
        "%s/system.reg" % common.ENV['WINEPREFIX'],
        # Newer versions of Wine don't create the userdef.reg file anymore.
        #"%s/userdef.reg" % common.ENV['WINEPREFIX'],
        "%s/user.reg" % common.ENV['WINEPREFIX'],
    ]
    return all([os.path.exists(path) for path in paths])

def winetricks_installed():
    """"Return the path to winetricks, if installed, else return False.
Also checks if winetricks is actually a shell script."""
    winetricks_path = common.which('winetricks')
    if winetricks_path:
        return winetricks_path

    winetricks_path = '%s/winetricks.sh' % common.ENV['VINEYARDPATH']

    if os.access(winetricks_path, os.R_OK) and os.path.getsize(winetricks_path):
        with open(winetricks_path, 'r') as file_obj:
            content = file_obj.read()
            if '#!' in content:
                runner = content[content.find('#!'):].split('\n')[0]
                if (
                    runner.endswith('sh') or
                    runner.endswith('bash') or
                    runner.endswith('dash')
                ):
                    return winetricks_path
    return False

def update_winetricks():
    import urllib
    winetricks_uri = 'http://winezeug.googlecode.com/svn/trunk/winetricks'

    winetricks_path = '%s/winetricks.sh' % common.ENV['VINEYARDPATH']
    urllib.urlretrieve(winetricks_uri, winetricks_path)
    return winetricks_path


def run_winetricks(arguments, shell_output=False, output_to_files=False):
    """
    Run (and possibly download winetricks first) winetricks with arguments.
    arguments has to be of type list."""

    if shell_output is True and output_to_files is True:
        raise Exception, "shell_output and output_to_files can't both be True"

    winetricks_path = winetricks_installed()
    if not winetricks_path:
        winetricks_path = update_winetricks()

    return monitor.Winetricks(
        arguments,
        name = ', '.join(arguments),
        env = common.ENV,
        executable = winetricks_path
    )

def _get_run_directory_from_possible_paths(possible_paths):
    run_in_path = None
    # Get the last file argument and also get the base path for run_in_path
    if len(possible_paths):
        for index, path in possible_paths:
            # Use the first existing path as the run_in_path variable
            # This ensures using the path to the executable, not the argument
            if util.path_exists(path):
                run_in_path = os.path.dirname(util.wintounix(path))
                break
        last_file_arg = util.unixtowin(possible_paths[-1][1])
        last_file_arg_index = possible_paths[-1][0]
    else:
        last_file_arg = None
        last_file_arg_index = None
    return (last_file_arg, last_file_arg_index, run_in_path)

def parse_command(command, env=None, run_in_path=None):
    """
    Parse a command, outputting a dict containing executable, arguments,
    environment and so on.
    Commands that have better XDG replacements are replaced.
    command can be list (preferably) or string,"""

    run_in_path_override = run_in_path

    # If command is given as a string
    if type(command) in (str, unicode):
        if util.path_exists(command):
            command = [command]
        elif util.path_exists(util.unescape_string(command)):
            command = [util.unescape_string(command)]
        else:
            command = util.string_split(
                command,
                retain_defines=True,
                remove_escapes=True
            )
    else:
        # This is a list, meaning it has to be preparsed, don't change it
        command = command[:] # make a copy, not a link

    # These variables are reported back in a dict
    wine_prefix = None      # WINEPREFIX, will be set in environment
    executable = None       # The executable to run, usually returns wine
    internal = False        # If True, don't monitor since nothing should go wrong
    if env is None or type(env) is not dict:
        env = common.ENV.copy() # Self-explanatory - except that any 'env'-command will alter it
    run_in_path = None      # Start the command in this path
    name = None             # Name will be set to something explanatory, like "Console"

    # Remove double backslashes
    command = [ i.replace('\\\\', '\\') for i in command ]

    print("Command split to", command)
    # Move any env definitions to the env dict
    if command[0] == 'env':
        for index, arg in enumerate(command[1:]):
            if '=' in arg:
                key = arg.split('=')[0]
                value = '='.join(arg.split('=')[1:])
                if len(value) and value[0] in ('"', "'"):
                    value = value[1:-1]
                env[key] = value
            else:
                break
        command = command[1+index:]
    if command[0] == 'wine' or command[0] == common.ENV['WINE'] or re.search(r'/.*/wine$', command[0]) is not None:
        del command[0]
        executable = common.ENV['WINE']
    if len(command) == 1:
        command[0] = util.string_remove_escapes(command[0])

    # Find all file and directory paths in the command
    possible_paths = []
    for index, i in enumerate(command):
        if i[1:3] == ':\\':
            possible_paths.append((index, i))
        elif i[0] == '/':
            if os.path.exists(i):
                possible_paths.append((index, i))
            elif os.path.exists(util.unescape_string(i)):
                possible_paths.append((index, util.unescape_string(i)))
                command[index] = util.unescape_string(i)
    #print("POSSIBLE PATHS:",possible_paths)

    last_file_arg, last_file_arg_index, run_in_path = (
        _get_run_directory_from_possible_paths(possible_paths)
    )
    print("possible paths: ",possible_paths)

    first_command = command[0].lower()
    #print("FIRST:",first_command)

    #print("LAST EXE:", last_file_arg)


    # Known, simple commands that don't require parsing
    if first_command in ('sh', 'env'):
        # Don't parse this command, it's shell magic
        executable = command[1]
        command = command[2:]
        name = "Shell command"
    elif first_command == 'winetricks':
        # Get the path for winetricks, if it exists
        winetricks = winetricks_installed()
        if winetricks:
            command[0] = winetricks
        internal = True

    # More advanced/troublesome commands
    else:
        command_lowercase = [ i.lower() for i in command ]

        # If internal command
        if (
            first_command.split('.')[-1] in common.BUILTIN_EXECUTABLES
        ) or (
            first_command[2:].startswith('\\windows\\command\\') and
            first_command.split('\\')[-1].split('.')[0] in common.BUILTIN_EXECUTABLES
        ):
            first_command_name = first_command.split('\\')[-1].split('.')[0]

            # Check for command being for a program that should be run in a command console
            if first_command_name == 'cmd':
                if len(command) > 1:
                    name = "Console: {0}".format(command[1])
                else:
                    name = "Console"
                command = [
                    'wineconsole', '--backend=user', 'cmd'
                ] + command[1:]

            elif first_command_name == 'regedit':
                name = "Regedit"
                internal = True

            # Override start.exe opening directories or URL, use xdg-open
            elif first_command_name == 'start':
                #print(command_lowercase)
                if '/unix' in command_lowercase:
                    # This is already a unix path, don't convert
                    # Select the argument after '/unix'
                    path = command[
                        command_lowercase.index('/unix')+1
                    ]
                    # Convert that argument to a UNIX path
                    path = util.wintounix(util.unixtowin(util.string_remove_escapes(path)))
                else:
                    if len(possible_paths):
                        # This is supposedly a Windows path, use the grabbed path
                        path = util.wintounix(possible_paths[0][1])
                    elif len(command) > 1:
                        # We couldn't grab a path, use first argument
                        path = command[1]
                    else:
                        # All is lost, assume 'start' is the actual command
                        path = command[0]

                try:
                    #link = parsers.read_lnk_file(path)
                    link = binary.windows_link(path)
                    if link and 'location' in link:
                        path = link['location']
                        if 'work dir' in link:
                            run_in_path_override = link['work dir']
                except IOError:
                    pass

                # Only use this path if it's actually a URL or directory
                if (
                    '://' in path[:8] or
                    os.path.isdir(util.wintounix(path))
                ):
                    print("start.exe was asked to open a directory or URL, use xdg-open instead")
                    executable = 'xdg-open'
                    command = [path]
                    run_in_path = None
                    internal = True
                else:
                    # This is a command that should be run, get run_in_path
                    run_in_path = (
                        _get_run_directory_from_possible_paths(
                            [(0, path)]
                        )
                    )[2]


    # Check for supported file types
    if last_file_arg is not None:
        if last_file_arg.endswith('.cpl'):
            if not first_command.endswith('control'):
                command = ['control'] + command[1:]
            name = "Control Panel"
            internal = True

        elif last_file_arg.endswith('.lnk'):
            # This is a Windows shell link, read the target and open that directly
            try:
                #link = parsers.read_lnk_file(util.wintounix(last_file_arg))
                link = binary.windows_link(util.wintounix(last_file_arg))
            except:
                link = False
            if link:
                # Convert link to a unix path and back to deal with Wine's
                # inability to handle Windows "wildcards" (the tilde character)
                link_win = util.unixtowin(util.wintounix(link['location']))

                link_unix = util.wintounix(link_win)

                if 'work dir' in link:
                    run_in_path_override = util.wintounix(link['work dir'])

                # If the file type is not handled by Wine normally,
                # then open it with xdg-open
                if (
                    os.path.exists(link_unix) and
                    util.file_get_mimetype(link_unix) not in common.WINDOWS_FORMATS
                ):
                    print("Not normal Windows format, using xdg-open instead: ", util.file_get_mimetype(link_unix))
                    executable = 'xdg-open'
                    command = [link_unix]
                    run_in_path = None
                    internal = True
                else:
                    # Change the .lnk filename to the one it's pointing to
                    command[last_file_arg_index] = link_win

                    remaining_args = [
                        i.lower() for i in command
                        if (
                            i != link_win and
                            not i.lower().endswith('start') and
                            not i.lower().endswith('start.exe')
                        )
                    ]
                    # This is just a call to a normal file, we can handle that
                    if remaining_args == ['/unix']:
                        if 'work dir' in link:
                            parsed_command = parse_command(
                                [link_win],
                                env,
                                run_in_path = util.wintounix(link['work dir'])
                            )
                        else:
                            parsed_command = parse_command(
                                [link_win],
                                env
                            )
                        return parsed_command

        elif last_file_arg.endswith('.msi'):
            # This is a Windows Installer, run in and monitor it
            command = ['msiexec', '/i'] + command
            name = "Installer"

        elif last_file_arg.endswith('.url'):
            if last_file_arg[1:].startswith(':\\'):
                url_filename = util.wintounix(last_file_arg)
                with open(url_filename, 'r') as url_fileobj:
                    url = url_fileobj.read()
                url = re.search(r'(?im)\[InternetShortcut\]\s+URL=(.*?)\s+?$', url)
                if url:
                    #print("It checks out, run it.")
                    # This is a URL, open it in a web browser, of course without monitoring it
                    url = url.groups()[0]
                    executable = 'xdg-open'
                    command = [url]
                    run_in_path = None
                    internal = True

    for index, argument in enumerate(command):
            command[index] = util.enhance_windows_path(
                command[index]
            )

    if run_in_path_override:
        run_in_path = run_in_path_override
    print("Run in", run_in_path)
    print("Env (changes):", util.dict_diff(os.environ, env))
    print({
        'command': executable,
        'arguments': command,
        'internal': internal,
        'prefix': wine_prefix,
        'env': env,
        'path': run_in_path,
        'name': name
        # Debug variables
        ,'_possible_paths': possible_paths
        ,'_last_file': last_file_arg
    })
    return {
        'command': executable,
        'arguments': command,
        'internal': internal,
        'prefix': wine_prefix,
        'env': env,
        'path': run_in_path,
        'name': name
        # Debug variables
        ,'_possible_paths': possible_paths
        ,'_last_file': last_file_arg
    }


def run(command, run_in_dir=True, dont_run=False, monitor=True, shell_output=False, name=None, use_terminal=False, disable_pulseaudio=False, cpu_limit=None):
    """Intelligently runs a Windows program.
This function also handles start.exe arguments (like web links), .msi installers and provides
the alias "cmd" for launching the wineconsole and "winetricks" for running, and optionally downloading
winetricks, with arguments.
Note that disable_pulseaudio only works when use_terminal is True."""

    command = parse_command(command)

    if 'VINEYARD_NO_MONITORING' in command['env']:
        monitor = False

    if monitor and shell_output:
        error("monitor and shell_output can't both be True, disabling shell_output")
        shell_output = False

    # Override any WINEPREFIX defined by command
    command['env']['WINEPREFIX'] = common.ENV['WINEPREFIX']

    # Create a new environment dict from our internal one
    env = common.copy(common.ENV)
    # Update it with the command's environment
    env.update(command['env'])

    if name is not None:
        command['name'] = name

    kwargs = {
        'env': env,
    }

    if command['command'] is None:
        command['command'] = common.ENV['WINE']

    if run_in_dir and command['path'] is not None:
        kwargs['cwd'] = command['path']

    if cpu_limit is not None:
        if type(cpu_limit) is int:
            kwargs['cpu_limit'] = cpu_limit
        elif cpu_limit is True:
            kwargs['cpu_limit'] = 1


    if monitor:
        kwargs['output_to_shell'] = False
        kwargs['use_log'] = True
        kwargs['name'] = command['name']
        kwargs['executable'] = command['command']

        if dont_run:
            return ('Monitor', command['arguments'], kwargs)
        else:
            if use_terminal:
                return util.open_terminal(
                    cwd = kwargs.get('cwd', None),
                    configuration_name = name,
                    cmd = command['command'],
                    arguments = command['arguments'],
                    disable_pulseaudio = disable_pulseaudio,
                    keep_open = True
                )
            else:
                return sys.modules['wine.monitor'].Program(
                    command['arguments'],
                    **kwargs
                )
    else:
        command_list = [command['command']] + command['arguments']

        if shell_output:
            kwargs['stdout'] = sys.stdout
            kwargs['stderr'] = sys.stderr

        if dont_run:
            return ('Run', command_list, kwargs)
        else:
            if use_terminal:
                return util.open_terminal(
                    cwd = kwargs.get('cwd', None),
                    configuration_name = name,
                    cmd = command['command'],
                    arguments = command_list,
                    disable_pulseaudio = disable_pulseaudio,
                    keep_open = True
                )
            else:
                return common.Popen(
                    command_list,
                    **kwargs
                )
