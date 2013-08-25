#!/bin/sh
path="$(dirname "$0")/../"

for i in "$path/po/"*.po; do
	language=$(basename $i | cut -d. -f1)
	if [ ! -d "$path/data/locale/$language" ]; then
		mkdir -p "$path/data/locale/$language/LC_MESSAGES"
	fi
	msgfmt $i -o "$path/data/locale/$language/LC_MESSAGES/vineyard.mo"
done
