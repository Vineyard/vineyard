#!/bin/bash

if [ -z "$(which pychecker)" ]; then
	echo -e "PyChecker doesn't seem to be installed.\nYou can download it from http://pychecker.sourceforge.net/"
	exit 1
fi

path="$(readlink -f "$(dirname "$0")/../")"

# pychecker needs a .py ending, so we create a symlink
ln -s "$path/vineyard-preferences" "$path/vineyard-preferences.py"

# run pychecker with the local data dir in the module search path
env PYTHONPATH="$path:$path/data:$PYTHONPATH" pychecker -q --limit 15 "$path/vineyard-preferences.py"

# we're done, remove the symlink
rm "$path/vineyard-preferences.py*"
