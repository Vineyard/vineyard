#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>
#
# Cache provides a simple dict like object.
# The cache that is queried will always follow the environment variable WINEPREFIX,
# meaning that if you set a value and then change WINEPREFIX, the value will not be
# found until you set WINEPREFIX back to its previous value.
#
# Any value set in the cache has an identifier included that corresponds to the
# md5 sum of the .reg files (system.reg, userdef.reg and user.reg) in WINEPREFIX.
#
# If the identifier on a set value in the cache does not match the current md5 sum
# of the .reg files, the value/key will be reported as not set.
# This way you can always be sure that any value in the cache is up to date with the
# registry database.

import os, cPickle, copy, hashlib, re
from threading import Lock
import common

pickle = cPickle

class Cache:
    def __init__(self):
        self.__version = 0.1
        self.__lock = Lock()
        self.__dict = {}
        self.__currentbottle = None
        self.__dict[None] = [0, {}]
        self.__read_file_cache()
    
    
    def __getitem__(self, key):
        if self.__contains__(key):
            value = self.__dict[self.__currentbottle][1][key]
        else:
            raise KeyError, key
        return copy.copy(value)
    
    def get(self, key):
        """ Return the value no matter if it's up to date or not """
        if self.__contains__(key, check_identifier=False):
            value = self.__dict[self.__currentbottle][1][key]
        else:
            raise KeyError, key
        retvalue = value
        return retvalue
     
    def __setitem__(self, key, value, update=True):
        try:
            if self.__dict[self.__currentbottle][1][key] == value:
                return True
        except KeyError:
            pass
        self.__read_file_cache()
        if type(value) == dict:
            self.__dict[self.__currentbottle][1][key] = value.copy()
        else:
            self.__dict[self.__currentbottle][1][key] = value
        if update:
            self.changed()
    
    def __delitem__(self, key):
        try:
            del self.__dict[self.__currentbottle][1][key]
            self.changed()
        except KeyError:
            return None
    
    def __contains__(self, key, check_identifier=True):
        self.__read_file_cache()
        retvalue = key in self.__dict[self.__currentbottle][1] and self.__dict[self.__currentbottle][0] == self.__get_update_time()
        return retvalue
    
    def save(self, dict):
        for key, value in dict.iteritems():
            self.__setitem__(key, value, update=False)
        self.changed()
    
    def current(self):
        # Checking if cache is up to date...
        self.__read_file_cache()
        return self.__dict[self.__currentbottle][0] == self.__get_update_time()
    
    def changed(self):
        self.__write_file_cache()
    
    def copy(self):
        self.__read_file_cache()
        retvalue = copy.deepcopy(self.__dict[self.__currentbottle][1])
        return retvalue
    
    def clear(self):
        try:
            os.remove("%s/.pythonwinecache" % self.__currentbottle)
        except OSError:
            pass
        self.__currentbottle = None
    
    def __get_update_time(self):
        # Read all .reg files, remove the timestamps from the content of the files (the regex) and match that to our cached md5 sum
        combined_reg = ""
        for regfile in ['system.reg', 'userdef.reg', 'user.reg']:
            if os.access("%s/%s" % (self.__currentbottle, regfile), os.W_OK):
                f = open("%s/%s" % (self.__currentbottle, regfile), 'r')
                combined_reg += re.sub(r'(?m)^(\[[^\]\n\r]+\]) \d+(\s+)?$',r'\1', f.read() )
                f.close()
        md5 = hashlib.md5()
        md5.update(combined_reg)
        return md5.hexdigest()
    
    
    def __read_file_cache(self, lock=True):
        if lock:
            self.__lock.acquire()
        # Check if WINEPREFIX has changed and only update the cache if it has
        if self.__currentbottle != common.ENV['WINEPREFIX']:
            self.__currentbottle = common.ENV['WINEPREFIX']
            
            cachefilename = "%s/.pythonwinecache" % self.__currentbottle
            if os.access(cachefilename, os.R_OK):
                #print "\tCache file exists, reading..."
                self.__filecache_file = open(cachefilename, 'rb')
                try:
                    self.__dict[self.__currentbottle] = pickle.load(self.__filecache_file)
                    #print "\tCache file read. Timestamp is %s." % self.__dict[self.__currentbottle][0]
                except:
                    self.__dict[self.__currentbottle] = [0, {}]
                    #print "\tSomething went wrong, resetting cache."
                self.__filecache_file.close()
                if '__version__' not in self.__dict[self.__currentbottle][1] or self.__dict[self.__currentbottle][1]['__version__'] < self.__version:
                    self.__dict[self.__currentbottle] = [0, {}]
            else:
                #print "\tNo cache file found, using blank."
                self.__dict[self.__currentbottle] = [0, {}]
        if lock:
            self.__lock.release()
    
    def __write_file_cache(self):
        self.__lock.acquire()
        if self.__currentbottle != common.ENV['WINEPREFIX']:
            self.__read_file_cache(lock=False)
        
        self.__dict[self.__currentbottle][0] = self.__get_update_time()
        self.__dict[self.__currentbottle][1]['__version__'] = self.__version
        try:
            self.__filecache_file = open("%s/.pythonwinecache" % self.__currentbottle, 'wb')
            pickle.dump(copy.deepcopy(self.__dict[self.__currentbottle]), self.__filecache_file)
            self.__filecache_file.close()
        except IOError:
            print "Current configuration is set wrong: %s" % self.__currentbottle
        self.__lock.release()
