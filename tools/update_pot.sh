#!/bin/sh
path="$(dirname "$0")/../"
filename="$(basename "$1")"

if [ -f "$path/data/$filename.glade" ]; then
	intltool-extract --type=gettext/glade "$path/data/$filename.glade"
	xgettext --from-code utf-8 -k_ -kN_ -o messages.pot "$path/$filename.py" "$path/data/$filename.glade.h"
else
	xgettext --from-code utf-8 -k_ -kN_ -o messages.pot "$path/$filename.py"
fi
