#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# Originally based on dannipenguin's threaded queue code
# (http://dannipenguin.livejournal.com/288663.html)
#
#
"""
Threads:
    · Fast to launch
    · Shares all data
    · Not always safe to use with Gtk
    · Poor multi-processor use.
    
    Conclusion: Use for GUI updates, small/fast utility programs (like wget) and the likes.

Processes:
    · (Possibly) slow to launch
    · Shares no data (can share simple objects through a manager though)
    · Perfectly safe to use alongside Gtk
    · Fine multi-processor use.
    
    Conclusion: Use for heavier program launching (Wine programs, not short use of regedit though).

++++++++
Thought:
++++++++
    Maybe we can run a Windows cmd in the background, interfacing with it through pexpect,
    in order to do regedit stuff?
    
    Run: wine cmd
    To write, send: regedit filename
    To read,  send: regedit /E tempfile.reg regpath
    
    THIS IS A GREAT IDEA!!! DO IT!!! :D
    
    ...easier said than done... regedit does not like being interfaced with and
    gives inconsistent output.
    """

from multiprocessing import Process, Queue
from threading import Thread as _Thread
#from Queue import Queue
import sys, traceback, types

def _print_exception_details():
    et, ev, tb = sys.exc_info()
    while tb:
        co = tb.tb_frame.f_code
        filename = str(co.co_filename)
        line_no =  str(traceback.tb_lineno(tb))
        print "%s:%s" % (filename, line_no)
        tb = tb.tb_next
    print "%s: %s" % (et, ev)


class _WorkerClass(object):
    _use_processes = True
    
    def __init__(self, *args, **kwargs):
        if 'use_processes' in kwargs:
            self._use_processes = kwargs['use_processes']
            del kwargs['use_processes']
        
    def _setup_main_queue(self):
        self._queue = Queue()
        
        if self._use_processes is True:
            t = Process(target=self._process_queue)
        else:
            t = _Thread(target=self._process_queue)
        t.name = "Queue"
        t.daemon = True
        t.start()
        print "Queue started", t
    
    def _process_queue(self):
        while 1:
            print "Processing queue... Size is", self._queue.qsize()
            request = self._queue.get()
            print "Request is:",request
            self._do_request(request)
            self._queue.task_done()
    
    def _do_request(self, function, *args, **kwargs):
        if type(function) == type(()):
            function, args, kwargs = function[:]
        if 'callback' in kwargs:
            callback = kwargs['callback']
            del kwargs['callback']
        else:
            callback = None

        if 'error' in kwargs:
            error = kwargs['error']
            del kwargs['error']
        else:
            error = None
        
        print "Run", function, args, kwargs
        try:
            r = function(*args, **kwargs)
            if not isinstance(r, tuple): r = (r,)
            if callback: self._do_callback(callback, *r)
        except Exception as e:
            print "Error occured"
            if error:
                self._do_callback(error, e)
            else:
                print "There was an error running the threaded function:", e
                print _print_exception_details()
    
    def _start_request_in_new_thread(self, function, *args, **kwargs):
        if self._use_processes is True:
            t = Process(target=self.__do_request, args=(function,)+args, kwargs=kwargs)
        else:
            t = _Thread(target=self.__do_request, args=(function,)+args, kwargs=kwargs)
        t.daemon = True
        t.start()
    
    def _add_request_to_main_queue(self, function, *args, **kwargs):
        try:
            getattr(self, '_queue')
        except AttributeError:
            self._setup_main_queue()

        self._queue.put((function, args, kwargs))
        print "Request added to queue. Size is now", self._queue.qsize()
    
    def _do_callback(self, callback, *args):
        def _callback(callback, args):
            callback(*args)
            return False

        _callback(callback, args)


class Worker(_WorkerClass):
    def __init__(self, *args, **kwargs):
        _WorkerClass.__init__(self, *args, **kwargs)
        
        # If the first argument is a function or method, run it in a new thread/process
        if len(args) and type(args[0]) in (types.FunctionType, types.MethodType):
            self.run(self, args[0], *args[1:], **kwargs)
        # Else, assume we are running as a queueing class
        else:
            self._setup_main_queue()
    
    def run(self, function, *args, **kwargs):
        self._start_request_in_new_thread(function, *args, **kwargs)
    
    def queue(self, function, *args, **kwargs):
        self._add_request_to_main_queue(function, *args, **kwargs)


def queued_method(func):
    """ Makes the given function be added to the separate thread/process queue.
        Use with decorators.
    """

    def bound_func(obj, *args, **kwargs):
        obj._add_request_to_main_queue(func, obj, *args, **kwargs)

    return bound_func

def spawned_method(func):
    """ Makes the given function be run in a separate thread/process.
        Use with decorators.
    """

    def bound_func(obj, *args, **kwargs):
        obj._start_request_in_new_thread(func, obj, *args, **kwargs)

    return bound_func



# Example of use:
if __name__ == '__main__':
    import time
    
    class MainApp(Worker):
        def __init__(self):
            self.printStuff('a', callback=self.donePrinting)
            print "Starting b"
            self.printStuff('b', callback=self.donePrinting)
            self.printStuff('c', callback=self.donePrinting)
            time.sleep(1)
        
        @queued_method
        def printStuff(self, stuff):
            for i in range(5):
                print stuff
            return True
        
        def donePrinting(self, return_code):
            if return_code:
                print "Done"
            else:
                print "Failed"

    app = MainApp()
