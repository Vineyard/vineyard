#!/usr/bin/python

import pexpect, sys
import os
import pprint
import re
import multiprocessing
import time

cwd = os.path.abspath(os.path.dirname(sys.argv[0]))
add_path = os.path.realpath('%s/python-wine' % cwd)
sys.path.insert(0, add_path)

from wine import util
import wine

class _Run():
    def __init__(self, command, timeout=-1, withexitstatus=False, events=None,
        extra_args=None, logfile=None, logfile_read=None, cwd=None, env=None, callback=None):
        """
        Much the same as run() from pexpect except that it uses our async module so it's
        asynchronous and can take the "command" argument as a list as well as a string.
        Also, it supports the logfile_read argument that spawn() supports indirectly."""
        # Convert the command argument from either a list or a string to a command and its arguments
        if type(command) in [list, tuple, set]:
            parts = list(command)
            command, arguments = parts[0], list(parts[1:])
        elif type(command) in pexpect.types.StringTypes:
            command, arguments = str(command), []

        if timeout == -1:
            self.child = pexpect.spawn(command, arguments,
                maxread=2000, logfile=logfile, cwd=cwd, env=env)
        else:
            self.child = pexpect.spawn(command, arguments,
                timeout=timeout, maxread=2000, logfile=logfile, cwd=cwd, env=env)
        self._withexitstatus = withexitstatus
        self._logfile = logfile
        self._callback = callback
        if logfile_read is not None:
            self.child.logfile_read = logfile_read
        if events is not None:
            self._patterns = events.keys()
            self._responses = events.values()
        else:
            self._patterns=None # We assume that EOF or TIMEOUT will save us.
            self._responses=None
        self._monitor()
        self._exit()

    def _monitor(self):
        child_result_list = []
        event_count = 0
        child = self.child
        patterns = self._patterns
        responses = self._responses
        logfile = self._logfile
        while 1:
            try:
                index = child.expect(patterns)
                if type(child.after) in pexpect.types.StringTypes:
                    child_result_list.append(child.before + child.after)
                else: # child.after may have been a TIMEOUT or EOF, so don't cat those.
                    child_result_list.append(child.before)
                if type(responses[index]) in pexpect.types.StringTypes:
                    child.send(responses[index])
                elif type(responses[index]) in (pexpect.types.FunctionType, pexpect.types.MethodType):
                    callback_result = responses[index](locals())
                    # Is this right? The original pexpect function doesn't have
                    # this test but it seems right since we are not printing to sys.stdout.
                    if logfile is None:
                        pexpect.sys.stdout.flush()
                    if type(callback_result) in pexpect.types.StringTypes:
                        child.send(callback_result)
                    elif callback_result:
                        break
                else:
                    raise TypeError ('The callback must be a string, function or method type.')
                event_count = event_count + 1
            except pexpect.TIMEOUT, e:
                child_result_list.append(child.before)
                break
            except pexpect.EOF, e:
                child_result_list.append(child.before)
                break
        self._child_result = ''.join(child_result_list)

    def _exit(self):
        if self._withexitstatus:
            self.child.close()
            if type(self._callback) in (pexpect.types.FunctionType, pexpect.types.MethodType):
                self._callback(self._child_result, self.child.exitstatus)
        else:
            if type(self._callback) in (pexpect.types.FunctionType, pexpect.types.MethodType):
                self._callback(self._child_result)


class Cmd:
    def push(self, interrupt, *args, **kwargs):
        try:
            self._interrupts[interrupt](self, *args, **kwargs)
        except KeyError:
            print "Can't execute %s, it is not set." % interrupt
        except TypeError:
            print "Can't execute interrupt %s, it is not a function or method type." % interrupt

    def __init__(self, pipe, interrupts={}):
        self.COMMAND_VERSION = '0.0.0'
        self.CWD = ''
        self._at_prompt = False
        self._waiting_for_command_output = False
        self._pipe = pipe
        self._interrupts = interrupts
        self._start_cmd()

    def _start_cmd(self):
        with open('{0}/output'.format(common.ENV['VINEYARDTMP']), 'w') as f:
            _Run('wine cmd', events={
                r'(?i)CMD Version ([\d\.\-\w]+)\r\n': self._parse_version,
                r'(?i)(\w:\\.*)>': self._parse_prompt,
    #            '\r\n': self._parse_newline,
                '^wine: (.*)\r\n': self._parse_wine_message,
                pexpect.TIMEOUT: self._timeout
            }, timeout=1, logfile_read=f)

    def _check_for_command(self):

        def _c_run_command(data):
            print "Command received", self._at_prompt
            if self._at_prompt == True:
                self._at_prompt = False
                self._waiting_for_command_output = True
                return '%s\r\n' % data
            else:
                print "We are not at prompt, but received a command... help?"

        def _c_exit(data):
            sys.exit(data)

        if self._pipe.poll():
            req_type, req_data = self._pipe.recv()
            try:
                return {
                    'run command': _c_run_command,
                    'exit': _c_exit
                }[req_type](req_data)
            except KeyError:
                print "Unknown request: %s" % req_type

    def _parse_version(self, d):
        self.COMMAND_VERSION = d['child'].match.groups()[0]

    def _parse_prompt(self, d):
        if self.CWD == '':
            self._pipe.send(['running', True])

        self._at_prompt = True

        self.CWD = d['child'].match.group(1)

        if self._waiting_for_command_output == True:
            self._waiting_for_command_output = False
            self._pipe.send(['command output', d['child'].before])

        return self._check_for_command()

    def _parse_newline(self, d):
        print "Newline:",d['child_result_list']

    def _parse_wine_message(self, d):
        error = d['child'].match.group(1)
        print "Wine reports an error:", error
        if not d['child'].isalive():
            #self._namespace.running = False
            self._pipe.send(['running', False])

    def _timeout(self, d):
        return self._check_for_command()


class Regedit:
    def __init__(self):
        self._current_callback = None
        self.cmd = None
        self._request_queue = []
        self._child_running = None
        self._pipe, child_pipe = multiprocessing.Pipe()
        self._start_cmd(child_pipe, {'run': self._child_run})

    def _child_run(self, command):
        print "Child.Run | args:", self, command

    def _start_cmd(self, *args, **kwargs):
        def _process_start(*args, **kwargs):
            Cmd(*args, **kwargs)
            return

        self.child = multiprocessing.Process(
            target = _process_start,
            args = args,
            kwargs = kwargs)
        self.child.daemon = True
        self.child.start()
        while not self._pipe.poll():
            pass
        message = self._pipe.recv()
        if message[0] == 'running':
            self._child_running = message[1]

    def get(self, branch=''):
        if self._child_running != True:
            return None
        output_filename = util.tempname('python-wine-regedit-read-', 'reg')
        output_filename_win = util.unixtowin(output_filename)
        command = 'regedit /E %s %s' % (output_filename_win, branch)
        self._pipe.send(['run command', command])
        while not self._pipe.poll():
            message_type, message = self._pipe.recv()
            if message_type == 'command output':
                # What until no process is using the output file (that being regedit)
                while util.get_command_output(['fuser', output_filename]) != '':
                    time.sleep(0.1)
                with open(output_filename, 'r') as f:
                    output = f.read()
                os.remove(output_filename)
                return output
            else:
                print "Command failed with:", message_type, message
                return None


if __name__ == '__main__':
    reg = Regedit()
    #print "Reg-output:", reg.get('HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion')
    _time = time.time()
    output = reg.get('HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\URL')
    if len(output) < 400:
        print "Reg-output:", output
    else:
        print "Reg-output:", len(output)
    print "Output took: %s" % (time.time() - _time)

    _time = time.time()
    output = wine.registry.__get_branch('HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\URL', only_use_regedit = True)
    if type(output) == type(()):
        output = output[1]
    if len(output) < 400:
        print "Reg-output:", output
    else:
        print "Reg-output:", len(output)
    print "Output took: %s" % (time.time() - _time)
    print "Done"

