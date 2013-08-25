#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>
#
"""
Runs a given command or series of arguments through bash, correctly escaping the arguments.
"""
from __future__ import print_function

import util, time
from common import Popen, subprocess, os, sys
import common

class run:
    log_filename_out = None
    log_filename_err = None

    def __init__(self, arguments, name=None, env=-1, cwd=None, output_to_shell=False, use_logfiles=True):

        command_safe = False

        if type(arguments) in (list, tuple):
            self.command = escape_arguments_to_string(arguments)
            command_safe = True
        else:
            self.command = arguments[:]

        self.start_time = time.localtime()

        kwargs = {}
        if env == -1:
            kwargs['env'] = common.copy(common.ENV)
        else:
            kwargs['env'] = env
        if cwd is not None:
            kwargs['cwd'] = cwd
        if output_to_shell:
            kwargs['stdin'] = sys.stdin
            kwargs['stdout'] = sys.stdout
            kwargs['stderr'] = sys.stderr
        elif use_logfiles:
            # If we are not outputting to the shell
            # the output will be routed to two files in /tmp.
            conf_name = util.string_safe_chars(
                env.get('WINEPREFIXNAME', common.ENV.get('WINEPREFIXNAME', ''))
            )

            self.log_filename_base = '%s-%s-%s' % (
                conf_name,
                time.strftime('%Y-%m-%d-%H:%M:%S', self.start_time),
                util.string_random()
            )
            self.log_filename_out = '{tmppath}/run-process-{filename}.out'.format(
                tmppath = common.ENV['VINEYARDTMP'], filename = self.log_filename_base)
            self.log_filename_err = '{tmppath}/run-process-{filename}.err'.format(
                tmppath = common.ENV['VINEYARDTMP'], filename = self.log_filename_base)
            self.log_out_last_pos = 0
            self.log_err_last_pos = 0

            if command_safe:
                self.command = "%s 2>%s 1>%s" % (
                    self.command,
                    self.log_filename_err,
                    self.log_filename_out
                )
            else:
                self.command = "%s 2>%s 1>%s" % (
                    util.string_safe_shell(self.command),
                    self.log_filename_err,
                    self.log_filename_out
                )

        # Use a new process group for this process
        if 'preexec_fn' not in kwargs:
            kwargs['preexec_fn'] = os.setpgrp

        if 'env' in kwargs:
            self.shell = common.which(['dash', 'bash', 'sh'], kwargs['env'])
        else:
            self.shell = common.which(['dash', 'bash', 'sh'])

        print("Going to run:", self.shell, '-c', '--', 'exec %s' % self.command)

        self.child = Popen([
            self.shell, '-c', '--', 'exec %s' % self.command
        ], **kwargs)
        print("Running:", self.shell, '-c', '--', 'exec %s' % self.command)

        self._kwargs = kwargs

        self.pid = self.child.pid
        self.returncode = self.child.returncode
        self.send_signal = self.child.send_signal
        self.terminate = self.child.terminate
        self.kill = self.child.kill

    def communicate(self):
        """
        Wait for the child process to finish, then return the stdout and stderr
        of it as a tuple in the form of (stdout, stderr)."""
        if self.child.returncode != None: # Process has finished
            return None

        if self.log_filename_out == None:
            return self.child.communicate()
        else:
            self.child.communicate()
            return self.read(with_stdout=True, with_stderr=True, since_last=True)

    def read(self, size=-1, with_stdout = True, with_stderr = True, since_last=False):
        """
        Read the stdout and/or stderr of the child process.
        If since_last is true only the output given since the last read is returned.
        If since_last is false the entire output stream is returned."""
        return _read(self, size=size, with_stdout=with_stdout, with_stderr=with_stderr, since_last=since_last)

    def read_stdout(self, since_last=False):
        return self.read(with_stdout = True, with_stderr = False, since_last = since_last)

    def read_stderr(self, since_last=False):
        return self.read(with_stderr = True, with_stdout = False, since_last = since_last)

    def poll(self):
        """
        Check if child process has terminated. Set and return returncode attribute."""
        # poll() has already been run, return the already given returncode
        if self.returncode != None:
            return self.returncode

        self.returncode = self.child.poll()
        # If process has terminated, delete it's object so the process can be freed
        if self.returncode != None:
            del self.child
            self.child = None
        return self.returncode


def escape_arguments_to_string(arguments):
    new_arguments = ""
    for argument in arguments:
        _pass = False
        # Test argument for an bash special characters
        print("Argument:", argument)
        if argument.startswith("'") and argument.endswith("'"):
            _pass = True
        elif common.any_in_string(['&', '(', ')', ';', '|', "\n", '<', '>', "'", '!', '*', '$', '[', ']', '`', '\\', ' ', '$'], argument):
            print("\tSpecial characters detected")
            new_argument = argument.replace("'", "\\'")
            new_arguments = "%s '%s'" % (new_arguments, new_argument)
        #elif common.any_in_string(["'", '*', '$', '`', '\\'], argument):
        #    new_argument = argument.replace("'", "'\\''")
        #    new_arguments = "%s '%s'" % (new_arguments, new_argument)
        #elif ' ' in argument:
        #    new_arguments = "%s '%s'" % (new_arguments, argument)
        else:
            print("\tNo special characters, passing through.")
            _pass = True

        if _pass:
            new_arguments = "%s %s" % (new_arguments, argument)
        #new_arguments = "%s %s" % (new_arguments, util.string_safe_shell(argument))
    return new_arguments[1:]

def _read(obj, size=-1, with_stdout = True, with_stderr = True, since_last=False):
    """
    Read the stdout and/or stderr of the child process of obj.
    If since_last is true only the output given since the last read is returned.
    If since_last is false the entire output stream is returned."""
    if obj.log_filename_out == None:
        if with_stdout:
            out = obj.child.stdout.read(size)
        if with_stderr:
            err = obj.child.stderr.read(size)
    else:
        if with_stdout:
            with open(obj.log_filename_out, 'r') as file_obj:
                if since_last:
                    try:
                        file_obj.seek(obj.log_out_last_pos)
                    except IOError:
                        if obj.log_out_last_pos > 0: # If it's 0 probably nothing was written yet
                            print("Couldn't seek to file-position in stdout.", file=sys.stderr)
                out = file_obj.read()
                if len(out) and out[-1] == '\n':
                    out = out[:-1]
                obj.log_out_last_pos = file_obj.tell() - 1 # -1 since we don't want to count the EOF
        if with_stderr:
            with open(obj.log_filename_err, 'r') as file_obj:
                if since_last:
                    try:
                        file_obj.seek(obj.log_err_last_pos)
                    except IOError:
                        if obj.log_err_last_pos > 0: # If it's 0 probably nothing was written yet
                            print("Couldn't seek to file-position in stderr.", file=sys.stderr)
                err = file_obj.read()
                if len(err) and err[-1] == '\n':
                    err = err[:-1]
                obj.log_err_last_pos = file_obj.tell() - 1 # -1 since we don't want to count the EOF

    if with_stdout and with_stderr:
        return (out, err)
    elif with_stdout:
        return out
    elif with_stderr:
        return err
