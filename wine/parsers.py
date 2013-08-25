#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

from __future__ import print_function

import sys, os, re, codecs
from collections import defaultdict
import util

import logging as _logging

logging = _logging.getLogger("python-wine.parsers")
debug = logging.debug
error = logging.error

RE_SECTIONS = re.compile(
    '(?ms)^\[(?P<path>[^\]]+)\](?:\s\d+)?\s+(?P<section>.*?)(?=^\[)'
)
RE_SECTION_VALUES = re.compile(
    r'(?ms)^(?P<key>\"[^\"]*?\"|@)=(?P<value>.*?)(?=^\")'
)
RE_NON_HEX_VALUES = re.compile(r'(?i)[^a-z0-9,]')


def _error_serious(error_text="Couldn't read registry!", debug_info=None):
    print(
        "{0} "+ \
        "This is a serious error, please report this error along with "+ \
        "the following text at "+ \
        "https://bugs.launchpad.net/vineyard".format(
            error_text
        ),
    file=sys.stderr)
    if debug_output != None:
        print(debug_output, file=sys.stderr)

def _error_parsing(error_text="Error in parsing!", debug_info=None):
    print(
        "{0} "+ \
        "Please report this error along with "+ \
        "the following text at "+ \
        "https://bugs.launchpad.net/vineyard".format(
            error_text
        ),
    file=sys.stderr)
    if debug_output != None:
        print(debug_output, file=sys.stderr)


def read_lnk_file(filename):
    """
    Return the information contained in a Windows .lnk file.
    filename should be a unix path."""
    with open(filename, 'rb') as file_obj:
        content = file_obj.read()
        identifier = str(content[:4].replace('\x00', ''))
        if identifier != 'L':
            print(
                "{0} is not a valid .lnk file.".format(filename),
                file=sys.stderr
            )
            return None

        icon_number = content[44:48]
        ## The first filename will always be the link, if there is a second
        ## it is the icon.
        ## 64 is the length of the header, might as well skip it.
        first_filename = re.search(
            r'([a-zA-Z]:\\.*?)\x00',
            content[64:]
        )
        if first_filename:
            return first_filename.groups()[0]
        else:
            return None


class DesktopFile:
    def __init__(self, file_path=None):
        self.data = {}
        self.file_path = None
        if file_path is not None and os.path.exists(file_path):
            self.file_path = file_path
            self.read_from_file(file_path)

    def read_from_file(self, file_path):
        self.data = {}
        with open(file_path, 'r') as _file:
            for line in _file:
                if '=' in line:
                    value = '='.join(line.split('=')[1:])
                    if value[-1] in ('\n', '\r'):
                        value = value[:-1]
                    self.data[ line.split('=')[0] ] = value


    def write_to_file(self, file_path):
        content = '#!/usr/bin/env xdg-open\n[Desktop Entry]'
        for key in sorted(self.data.keys()):
            content = '{0}\n{1}={2}'.format(
                content, key, self.data[key]
            )
        with open(file_path, 'w') as _file:
            _file.write(content)

    def save(self):
        if self.file_path is not None:
            self.write_to_file(self.file_path)

    def __setitem__(self, key, value):
        if value is True:
            value = 'true'
        elif value is False:
            value = 'false'
        return self.data.__setitem__(key, value)

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data


def parse_registry_to_sections(registry_contents):
    return RE_SECTIONS.findall(registry_contents+'\n[')

def parse_registry_section_to_dict(section, return_dict=True):
    values = RE_SECTION_VALUES.findall(section+'"')
    section_dict = multidict()

    for key, value in values:
        """ Strip the start and end quotes """
        if key != '@':
            key = key[1:-1]
        value = parseValue(value)
        if type(value) == tuple:
            section_dict['_%s' % key] = value[0]
            section_dict[key] = value[1]
        else:
            section_dict[key] = value

    if return_dict:
        return section_dict.get_dict()
    else:
        return section_dict

def parseRegistry(registry, base_path=None, encoding='cp1252'):
    registry = parseInput(registry, encoding = encoding)
    registry_dict = multidict()
    sections = parse_registry_to_sections(registry)
    for path, section in sections:
        section_dict = parse_registry_section_to_dict(section, return_dict=False)
        try:
            exec_string = 'registry_dict{0} = section_dict'.format(
                ''.join((
                    #'[\'{0}\']'.format(i.encode('string_escape'))
                    '[\'{0}\']'.format(i.replace('\'', '\\\''))
                    for i in filter(len,path.split('\\'))
                ))
            )
            exec(exec_string)
        except Exception, err:
            if (str(path).strip().lower().replace('\\\\','\\')
            ).startswith('software\\classes\\directshow\\mediaobjects'):
                debug(
                    "Couldn't parse DirectShow MediaObjects registry info: "+ \
                    "duplicate name for key and branch."
                )
            else:
                _error_parsing(debug_info=(
                    '\n\t'.join([
                        'Exec: {0}'.format(exec_string),
                        'Path: {0}'.format(path),
                        'Registry-dict Type: {0}'.format(type(registry_dict)),
                        'Section-dict Type: {0}'.format(type(section_dict)),
                        'Error was: {0}'.format(err)
                    ])
                ))
            continue
    if base_path != None:
        return {base_path: registry_dict.get_dict()}
    else:
        return registry_dict.get_dict()

def parseValue(value):
    """ Convert a Windows Registry value to a Python value
        For more info about Windows Registry types, see:
        http://technet.microsoft.com/en-us/library/bb727154.aspx
    """
    original_value = None
    value_is_string = True
    value_type = value.split(':')[0].lower()
    if value_type.startswith('hex(2)'):
        """ Expanded String """
        try:
            new_value = util.hextoutf8(value)
            original_value = value
            value = new_value
        except UnicodeDecodeError:
            value_is_string = False
            _error_serious(debug_info = (
                path, key, value_type, value
            ))
            original_value = value
            value = "Error: Expanded String decoding error!"
    elif value_type.startswith('hex(7)'):
        """ Multi String """
        value_is_string = False
        try:
            value = filter(len, util.hextoutf8(value).split('\x00'))
        except TypeError:
            _error_serious(debug_info = (
                path, key, value_type, value
            ))
            original_value = value
            value = "Error: Multi String decoding error!"
    elif value_type.startswith('hex'):
        """ HEX Value """
        value_is_string = False
        value = '{key}:{value}'.format(
            key = value.split(':')[0],
            value = RE_NON_HEX_VALUES.sub('', ''.join(value.split(':')[1:]))
        )
    elif value_type.startswith('dword'):
        """ Double Word (displayed as HEX usually) """
        value_is_string = False
        value = value.strip()
    elif value_type.startswith('null'):
        value_is_string = False
        value = None
    elif value_type.startswith('str(2)'):
        """ Expandable String """
        value = ':'.join(value.strip().split(':')[1:])
    elif value_type.startswith('quote') or value.startswith('str'):
        value = ':'.join(value.strip().split(':')[1:])
    if value_is_string:
        if value.strip().startswith('"') and value.replace('\x00','').strip().endswith('"'):
            value = '"'.join(value.strip().split('"')[1:-1])
            value = value.replace('\\\\', '\\').replace('\\"', '"')
        """try:
            if type(value) == list:
                value = [ util.stringtoutf8(i) for i in value ]
            else:
                value = util.stringtoutf8(value)
        except UnicodeDecodeError:
            _error_serious(debug_info = (
                path, key, value_type, value.encode('hex')
            ))
            original_value = value
            value = "Error: String decoding error!" """
    if original_value != None:
        return (original_value, value)
    else:
        return value

def parseInput(input_object, encoding='cp1252'):
    """
        Takes either a file descriptor object, a file name or the contents of a
        file as an argument and returns the contents of it.
    """
    if type(input_object) == file:
        output = input_object.read()
    elif '\n' not in input_object and os.path.isfile(input_object):
        file_object = codecs.open(input_object, 'r', encoding=encoding)
        output = file_object.read()
        file_object.close()
    else:
        return input_object
    return output

class multidict(defaultdict):
    def __init__(self):
        self.default_factory = type(self)
    def get_dict(self):
        return self.__convert_to_dict(self)
    def __convert_to_dict(self, mdict):
        return_dict = {}
        for key,value in mdict.iteritems():
            if type(value) == type(self):
                return_dict[key] = self.__convert_to_dict(value)
            else:
                return_dict[key] = value
        return return_dict
