#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>
"""
Run a program in a separate thread and monitor its state.
When the program exits its output is analysed and any errors are tried to be explained.

Also, this module will keep a list of running programs so you can interact with any of them
during execution."""

from __future__ import print_function

import common, util, command, libraries, programs
import time, re, os, sys, signal, re, __builtin__

RUNNING_PROGRAMS = {}

# TODO: Change this to be loaded from a configuration file
NUMBER_OF_LOGS_TO_KEEP = 5

"""
    NOTES:
    Figure out if this thing works (the only Windows program that blocks on stdout is AvP3s installer).
"""

def list():
    update_list()
    return RUNNING_PROGRAMS.keys()

def get(name=None):
    if name == None:
        return get_all()
    update_list()
    return RUNNING_PROGRAMS[name]

def get_all():
    update_list()
    return RUNNING_PROGRAMS

def get_full_list():
    """Get a list of running as well as recently run programs."""
    # Get log files
    directory = '%s/process_info' % common.ENV['VINEYARDPATH']
    program_list = sorted(os.listdir(directory))
    program_dict = dict(
        (
            info_name,
            info
        )
        for info_name, info in (
            (
                info_name,
                AdoptedProgram(get_program_info(info_name))
            )
            for info_name in program_list
        )
        if info.has_log()
    )

    return program_dict

def update_list():
    # Update programs dict
    #print("Checking which programs are alive...")
    for name, program in RUNNING_PROGRAMS.items():
        if not program.is_alive():
            del RUNNING_PROGRAMS[name]
            #print("\t%s is terminated, removed." % name)
        else:
            pass
            #print("\t%s is still alive, leaving alone." % name)

    # Get log files
    directory = '%s/process_info' % common.ENV['VINEYARDPATH']
    program_list = sorted(os.listdir(directory))

    # Run through list of process info files and get the ones that aren't running anymore
    #print("Checking which info files are obsolete and adding still running programs...")
    old_programs = []
    pids_of_users_processes = util.get_pids_of_user_processes()
    for info_name in program_list:
        if info_name not in RUNNING_PROGRAMS:
            discard = True
            # Get the info contained in the info file
            info = get_program_info(info_name)
            if 'pid' in info and info['pid'] in pids_of_users_processes:
                # If the process with this PID was started at the same time
                # as our the process info's says, they are the same
                # process.
                # The matching of start time is done +-3 seconds
                # to account for any differences in logging between Vineyard
                # and the system.
                #print("We have a process with PID %s in our logs, checking if it's alive and ours..." % info['pid'])
                pid_stime = util.get_start_time_of_pid(info['pid'])
                if pid_stime != None:
                    (pid_stime_month, pid_stime_day,
                    pid_stime_hour, pid_stime_minute, pid_stime_second) = pid_stime

                    our_stime = _get_start_time_from_program_info(info)
                    (our_stime_month, our_stime_day,
                    our_stime_hour, our_stime_minute, our_stime_second) = our_stime
                    if (
                        pid_stime_month == 0 and
                        pid_stime_hour == our_stime_hour and
                        pid_stime_minute == our_stime_minute and
                        (
                            pid_stime_second == our_stime_second or
                            pid_stime_second == our_stime_second-1 or
                            pid_stime_second == our_stime_second+1 or
                            pid_stime_second == our_stime_second-2 or
                            pid_stime_second == our_stime_second+2 or
                            pid_stime_second == our_stime_second-3 or
                            pid_stime_second == our_stime_second+3
                        )
                    ) or (
                        pid_stime_month == our_stime_month and
                        pid_stime_day == our_stime_day
                    ):
                        #print("PID %s is ours." % info['pid'])
                        if util.get_state_code_of_pid(info['pid']) in ('Z', ''):
                            # This process is a zombie, let it rest in peace
                            #print("Let PID %s die." % info['pid'])
                            try:
                                os.waitpid(info['pid'], 0)
                            except OSError:
                                # Already exited
                                pass
                        else:
                            # This process is alive, add it to the list
                            RUNNING_PROGRAMS[info_name] = AdoptedProgram(info)
                            discard = False
            if discard:
                old_programs.append(info_name)

    # Remove the info files that aren't running and are more than is to be kept
    #print("Cleaning up old info files...")
    for info_name in old_programs[:-5]:
        try:
            #print("\t%s is no longer needed, removing...")
            os.remove('%s/%s' % (directory, info_name))
        except OSError:
            print("Couldn't remove process info file \"%s\"." % info_name, file=sys.stderr)

def _get_start_time_from_program_info(info):
    stime = info['start-time']
    return (stime.tm_mon, stime.tm_mday, stime.tm_hour, stime.tm_min, stime.tm_sec)

def get_program_info(info_name):
    directory = '%s/process_info' % common.ENV['VINEYARDPATH']

    try:
        if os.access(info_name, os.R_OK):
            file_name = info_name
        else:
            file_name = '%s/%s' % (directory, info_name)

        with open(file_name, 'r') as file_object:
            info_dict = {}
            for line in file_object:
                key = line.split(': ')[0]
                value = ': '.join(line.split(': ')[1:])
                if value[-1] == '\n':
                    value = value[:-1]
                if value.startswith('time.struct_time('):
                    # Discard the value, we got the time from the filename
                    value = time.strptime('-'.join(info_name.split('-')[-5:-1]), '%Y-%m-%d-%H:%M:%S')
                if key == 'pid':
                    value = int(value)
                if value == 'True' or value == 'False':
                    value = eval(value)
                info_dict[key] = value
        return info_dict
    except IOError:
        print("Can't read log process, log-file could not be opened.", file=sys.stderr)
        return {}

def explain_missing_dlls(error_string):
    """
    Returns a dict containing the missing DLLs as keys and lists
    containing the suggested packages containing the DLL as the
    values."""
    missing_dlls = []
    for line in error_string.split('\n'):
        match = re.match(r'(?i)^err:module:import_dll .*? (\w+\.\w{3})', line)
        if match:
            missing_dlls.append(match.groups()[0].lower())
    missing_dlls = __builtin__.list(set(missing_dlls))

    return_dict = {}
    # Figure out which packages we know contains the missing DLLs
    dll_packages = libraries.PACKAGES
    for dll in missing_dlls:
        packages_containing_dll = [
            k for (k, v)
            in dll_packages.iteritems()
            if dll.lower() in v
        ]
        return_dict[dll.lower()] = packages_containing_dll

    return return_dict

def explain_errors(error_string):
    missing_dlls = explain_missing_dlls(error_string)

    if len(missing_dlls):
        return_string = "The program is missing the following DLL files:%s" % (
            ''.join((
                '\n\t%s' % i for i in missing_dlls.keys()
            ))
        )

        return_string += "\nTry installing the following packages to fix the problem:"
        if len(missing_dlls) > 1:
            for dll, packages in missing_dlls.iteritems():
                return_string += '\n\t{package} to get {dll}'.format(
                    package = ' or '.join(packages),
                    dll = dll
                )
        else:
            for dll, packages in missing_dlls.iteritems():
                return_string += '\n\t{package}'.format(
                    package = ' or '.join(packages)
                )
        return return_string
    else:
        return None

def get_children(process):
    try:
        file_name = process.child.log_filename_err
    except:
        return []
    return util.get_pids_using_file(file_name)

def wait_for_children(process):
    while len(util.get_pids_of_pgid(process.pid)):
        time.sleep(0.5)
    while len(process.get_children()):
        time.sleep(1)
    return

class Program:
    def __init__(self, command_arg, name=None, env=None, cwd=None, executable='wine', output_to_shell=False, use_log=True, cpu_limit=None):
        """
        Run a program in a separate thread and monitor its state."""

        if output_to_shell is True and use_log is True:
            raise ValueError("output_to_shell and use_log can't both be True")

        if env is None:
            env = common.ENV
        if name is None:
            #name = command_arg.split()[0].split('\\')[-1]
            if type(command_arg) in (str, unicode):
                programs.isolate_executable_from_command(command_arg)
            else:
                name = command_arg[0]
            try:
                name = util.get_program_name(util.wintounix(name))
            except (IOError, TypeError):
                name = ''
        self.name = name

        print(executable)
        if executable is not None and len(executable):
            if executable == 'wine' and 'WINE' in env:
                executable = common.ENV['WINE']
            if type(command_arg) in (__builtin__.list, tuple):
                command_arg = [executable] + command_arg
            else:
                command_arg = "%s '%s'" % (executable, command_arg)
        print(executable)

        if cpu_limit is not None and type(cpu_limit) is int and cpu_limit > 0:
            if common.which('taskset'):
                command_arg = ['taskset', str(cpu_limit)] + command_arg
                print("Limiting process to {0} CPUs.".format(cpu_limit))
            else:
                print(("Couldn't limit process to {0} CPUs, " +
                        "taskset isn't installed."
                ), file=sys.stderr)

        self.has_standard_output = True

        self.prefix = env.get('WINEPREFIX', None)

        self.child = command.run(command_arg, name = name,
            env = env, cwd = cwd,
            output_to_shell = output_to_shell, use_logfiles = use_log
        )

        self.pid = self.child.pid
        self.start_time = self.child.start_time

        if use_log is True:
            self._create_info_file()
        RUNNING_PROGRAMS[self.child.log_filename_base] = self

        # Clean up RUNNING_PROGRAMS
        update_list()

    def __del__(self):
        """
        Don't keep the process as a zombie if it isn't running anymore."""
        try:
            self.child.poll()
        except AttributeError:
            pass

    def wait(self, explain=True):
        return_code = self.child.poll()
        while return_code == None:
            time.sleep(0.25)
            return_code = self.child.poll()

        if explain:
            return self.explain_errors()
        else:
            return return_code

    def wait_for_children(self):
        return wait_for_children(self)

    def read_stdout(self):
        return self.child.read_stdout()

    def read_stderr(self):
        return self.child.read_stderr()

    def explain_errors(self):
        return explain_errors(self.read_stderr())

    def explain_missing_dlls(self):
        return explain_missing_dlls(self.read_stderr())

    def send_signal(self, signal):
        return_code = self.child.send_signal(signal)
        update_list()
        return return_code

    def terminate(self):
        self.child.terminate()
        self.wait(explain=False)
        update_list()
        return return_code

    def kill(self):
        self.child.kill()
        return_code = self.wait(explain = False)
        update_list()
        return return_code

    def is_alive(self):
        return (self.child.poll() == None)

    def get_children(self):
        return get_children(self)

    def _create_info_file(self):
        directory = '%s/process_info' % common.ENV['VINEYARDPATH']
        if not (
            os.path.isdir(directory) and
            os.access(directory, os.R_OK & os.W_OK)
        ):
            try:
                os.mkdir(directory)
            except OSError:
                print("Can't log process, %s is not writable." % directory, file=sys.stderr)
                return False

        try:
            with open('%s/%s' % (directory, self.child.log_filename_base), 'w') as file_object:
                content = [
                    ('name', self.name),
                    ('pid', self.pid),
                    ('has standard output', self.has_standard_output),
                    ('start-time', self.start_time),
                    ('stdout-log', self.child.log_filename_out),
                    ('stderr-log', self.child.log_filename_err),
                    ('prefix', self.prefix)
                ]
                file_object.write('\n'.join('%s: %s' % (k, v) for (k, v) in content))
        except OSError:
            print("Can't log process, log-file could not be written to.", file=sys.stderr)
            return False


class AdoptedProgram:
    def __init__(self, name_or_info):
        if type(name_or_info) == dict:
            info = name_or_info
        elif type(name_or_info) == str:
            info = get_program_info(name_or_info)
        else:
            raise TypeError, "First argument should be either a program name as given by list() or an already parsed info dict."

        self.name = info['name']
        self.has_standard_output = info['has standard output']
        self.pid = info['pid']
        self.start_time = info['start-time']
        self.log_filename_out = info['stdout-log']
        self.log_filename_err = info['stderr-log']
        self.log_out_last_pos = 0
        self.log_err_last_pos = 0
        self.prefix = info['prefix']

    def __del__(self):
        """
        Don't keep the process as a zombie if it isn't running anymore."""
        try:
            if util.get_state_code_of_pid(self.pid) in ('Z', ''):
                os.waitpid(self.pid, 0)
        except OSError:
            pass

    def wait(self, explain=True):
        while self.is_alive():
            time.sleep(0.25)

        try:
            return_code = os.waitpid(self.pid, 0)[1]
        except OSError:
            # We couldn't read the return code, the process is already gone
            return_code = None

        if explain:
            return self.explain_errors()
        else:
            return return_code

    def wait_for_children(self):
        return wait_for_children(self)

    def has_log(self):
        return (
            os.path.exists(self.log_filename_out) and
            os.path.exists(self.log_filename_err)
        )

    def read_stdout(self, since_last=False):
        return command._read(self, with_stdout = True, with_stderr = False, since_last = since_last)

    def read_stderr(self, since_last=False):
        return command._read(self, with_stderr = True, with_stdout = False, since_last = since_last)

    def explain_errors(self):
        return explain_errors(self.read_stderr())

    def explain_missing_dlls(self):
        return explain_missing_dlls(self.read_stderr())

    def send_signal(self, signal):
        os.kill(self.pid, signal)
        update_list()

    def terminate(self):
        os.kill(self.pid, signal.SIGTERM)
        self.wait(explain=False)
        update_list()

    def kill(self):
        os.kill(self.pid, signal.SIGKILL)
        self.wait(explain=False)
        update_list()

    def is_alive(self):
        return (util.get_state_code_of_pid(self.pid) not in ('X', 'Z', ''))

    def get_children(self):
        return get_children(self)


class Winetricks(Program):
    def __init__(self, command_arg, name=None, env=None, cwd=None, executable='winetricks', output_to_shell=False, use_log=True):
        """
        Run a program in a separate thread and monitor its state."""

        if env is None:
            env = common.ENV
        if name is None:
            #name = command_arg.split()[0].split('\\')[-1]
            name = command_arg[0]
        self.name = name

        print(executable)
        if executable is not None and len(executable):
            if type(command_arg) in (__builtin__.list, tuple):
                command_arg = [executable] + command_arg
            else:
                command_arg = "%s -q '%s'" % (executable, command_arg)
        print(executable)

        self.has_standard_output = False

        self.prefix = env.get('WINEPREFIX', None)

        self.child = command.run(command_arg, name = name,
            env = env, cwd = cwd, output_to_shell = output_to_shell, use_logfiles = use_log
        )

        self.pid = self.child.pid
        self.start_time = self.child.start_time

        self.packages_already_installed = []
        self.status_download_procentage = 0

        if use_log == True:
            self._create_info_file()
        RUNNING_PROGRAMS[self.child.log_filename_base] = self

        # Clean up RUNNING_PROGRAMS
        update_list()

    def wait(self, explain = False):
        Program.wait(self, explain = explain)

    def wait_for_children(self):
        return wait_for_children(self)

    def get_children(self):
        return get_children(self)

    def get_output(self):
        std_output = self.read_stdout()
        std_lines = filter(len,
            ( i.strip() for i in std_output.split('\n') )
        )

        if len(std_lines):
            if 'Executing wget' in std_lines[-1]:
                # Status: Download initiated
                file_name = (
                    std_output.split('Executing wget')[1]
                ).split('-O ')[1].split(' -')[0].strip()

                # Get procentage of download from stderr
                std_error = self.read_stderr()

                procentage = None
                if '%' in std_error:
                    procentage = re.search('(?ms).*\s(\d{1,3})%', std_error)
                if procentage is None:
                    procentage = self.status_download_procentage
                else:
                    try:
                        procentage = int(procentage.groups()[0])
                        self.status_download_procentage = procentage
                    except ValueError:
                        procentage = self.status_download_procentage

                return ('downloading', file_name, procentage)
            else:
                self.status_download_procentage = 0
                if 'Executing ' in std_lines[-1]:
                    executable = '/'+std_lines[-1].split(' /')[-1]
                    return ('executing', executable)

                elif 'already installed' in std_lines[-1]:
                    # Status: Package already installed
                    if 'prerequisite' in std_output:
                        package = filter(len,
                            std_output.split('already installed')
                        )[0].split('prerequisite')[1].strip()
                    else:
                        package = filter(len,
                            std_output.split('already installed')
                        )[0].split('\n')[1].strip()
                    return ('already installed', package)

                elif 'Archive: ' in std_lines[-1]:
                    archive = ':'.join(std_lines[-1].split(':')[1]).strip()
                    return ('extracting', archive)

                elif ' regedit ' in std_lines[-1]:
                    return ('configuring')

                elif 'sha1sum mismatch!  Rename' in std_output:
                    file_path = (
                        std_output.split('sha1sum mismatch!  Rename ')[1]
                    ).split(' and try again.')[0]
                    return ('faulty file', file_path)

                elif 'Install of ' in std_lines[-1] and std_lines[-1].endswith('done'):
                    return ('success', ' done'.join(
                        std_lines[-1].split('Install of ')[1].split(' done')[:-1]
                    ))

                elif 'winetricks done.' in std_lines[-1]:
                    return ('done', )

                elif 'returned status' in std_output and 'Aborting.' in std_output:
                    return ('failed', std_output.split('returned status')[1].split('.')[0].strip())

