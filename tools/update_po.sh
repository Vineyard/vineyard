#!/bin/sh
path="$(dirname "$0")/../"

for i in "$path/po/"$1_*.po; do
	if [ -f $i ]; then
		msgmerge -U $i messages.pot
	fi
done
