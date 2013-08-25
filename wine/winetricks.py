# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

from __future__ import print_function

import common, util
import re


REGEX_STRING_VERBS_TEMPLATE = (
    '(?ms)^w_metadata (?P<name>[^ ]*) {cat} (?P<info>.*?)^\S'
)
REGEX_VERBS = {}
for category in (
    'apps',
    'benchmarks',
    'dlls',
    'fonts',
    'games',
    'settings'
):
    REGEX_VERBS[category] = re.compile(REGEX_STRING_VERBS_TEMPLATE.format(
        cat = category
    ))
REGEX_VERBS[None] = re.compile(REGEX_STRING_VERBS_TEMPLATE.format(
    cat = '\\S+'
))

def read_winetricks():
    winetricks = common.which('winetricks')
    with open(winetricks, 'r') as _file:
        data = _file.read()
    if 'w_metadata' not in data:
        raise EnvironmentError, "Winetricks is too old, can't parse."
    return data

def list_all(category=None):
    winetricks = read_winetricks()
    verbs = {}
    for name, info_str in re.findall(REGEX_VERBS[category], winetricks):
        info = {}
        info_iter = iter(util.string_split(info_str))
        for key in info_iter:
            value = next(info_iter, None)
            if value is None:
                break
            info[key[:-1]] = util.string_remove_escapes(value)
            verbs[name] = info
    return verbs
