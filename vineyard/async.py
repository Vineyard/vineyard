#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# Based on dannipenguin's threaded queue code at
# http://dannipenguin.livejournal.com/288663.html
#
# Example of use:
"""
class MainApp(ThreadedClass):
    def __init__(self):
        self.printStuff('a', callback=self.donePrinting)
        self.printStuff('b', callback=self.donePrinting)
        self.printStuff('c', callback=self.donePrinting)

    @async_method
    def printStuff(self, stuff):
        for i in range(5):
            print stuff

    def donePrinting(self, return_code):
        print "Done"

gobject.threads_init()
app = MainApp()
gtk.main()
"""

import threading
from Queue import Queue
#from multiprocessing import Process
from vineyard import crashhandler
import gobject
import sys
import traceback

def _print_exception_details():
    et, ev, tb = sys.exc_info()
    while tb:
        co = tb.tb_frame.f_code
        filename = str(co.co_filename)
        line_no =  str(traceback.tb_lineno(tb))
        print "%s:%s" % (filename, line_no)
        tb = tb.tb_next
    print "%s: %s" % (et, ev)

class ThreadedClass_base(object):
    type = ''

    def do_request(self, (function, args, kwargs)):
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

        try:
            r = function(*args, **kwargs)
            if not isinstance(r, tuple): r = (r,)
            if callback: self.do_callback(callback, *r)
        except Exception as e:
            print "Error occured"
            if error:
                self.do_callback(error, e)
            else:
                print "There was an error running the threaded function:", e
                print _print_exception_details()
                #crashhandler.show_error_window((
                #    "There was an error running the threaded function, "+
                #    "the error was:\n" +
                #    "{error}: {cause}"
                #).format(
                #    error = error,
                #    cause = e
                #))

    def do_callback(self, callback, *args):
        def _callback(callback, args):
            callback(*args)
            return False

        gobject.idle_add(_callback, callback, args)


THREAD_QUEUE = None
class ThreadedClass_queued_worker(ThreadedClass_base):
    def __init__(self):
        self.queue = Queue()

        thread = threading.Thread(target=self._thread_worker)
        thread.setDaemon(True)
        thread.start()

    def _thread_worker(self):
        while True:
            request = self.queue.get()
            self.do_request(request)
            self.queue.task_done()


class ThreadedClass_queued(ThreadedClass_base):
    type = 'queue'

    def __init__(self):
        global THREAD_QUEUE
        if THREAD_QUEUE is None:
            THREAD_QUEUE = ThreadedClass_queued_worker()

    def run_in_thread(self, func, *args, **kwargs):
        """Add a request to the queue. Pass callback= and/or error= as
           keyword arguments to receive return from functions or exceptions.
        """
        THREAD_QUEUE.queue.put((func, args, kwargs))


class ThreadedClass_multi(ThreadedClass_base):
    type = 'multi'

    def run_in_thread(self, function, *args, **kwargs):
        threading.Thread(target=self.do_request, args=((function, args, kwargs),)).start()


def async_method(func):
    """ Makes the given function be run in a separate thread.
        Use with decorators.
    """

    def bound_func(obj, *args, **kwargs):
        obj.run_in_thread(func, obj, *args, **kwargs)

    return bound_func

def run_in_thread(func, *args, **kwargs):
    thread = ThreadedClass_multi()
    thread.run_in_thread(
        func, *args, **kwargs
    )

def mainloop_method(func):
    def wrapped_func(*args, **kwargs):
        return gobject.idle_add(idle_func, *args, **kwargs)

    def idle_func(*args, **kwargs):
        func(*args, **kwargs)
        return False

    return idle_func

def execute_in_mainloop(*args, **kwargs):
    def _function():
        try:
            args[0](*args[1:], **kwargs)
        except TypeError:
            print "Couldn't run function in mainloop! Arguments were: "+\
                   "{0}({1}, {2}".format(args[0], args[1:], kwargs)
        return False
    gobject.idle_add(_function)

def get_number_of_running_threads():
    if ThreadedClass.type == 'queue':
        global THREAD_QUEUE
        if THREAD_QUEUE is not None:
            len_of_queue = THREAD_QUEUE.queue.qsize()
            if THREAD_QUEUE.queue.unfinished_tasks:
                if len_of_queue < 1:
                    return 1
                else:
                    return len_of_queue
            else:
                return 0
        else:
            return 0
    elif ThreadedClass.type == 'multi':
        return threading.active_count() - 1
    else:
        return 0

# Set default thread class
class ThreadedClass(ThreadedClass_queued):
    pass
