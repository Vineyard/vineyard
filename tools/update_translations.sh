#!/bin/sh
path="$(readlink -f "$(dirname "$0")/../")"

echo -n "Extracting translatable strings..."
cd "$path"
intltool-extract --type=gettext/glade \
  "data/vineyard-preferences.glade" \
1>/dev/null
xgettext --language Python --from-code utf-8 -k_ -kN_ -o "$path/po/vineyard.pot" \
  "$path/vineyard-preferences" \
  "$path/vineyard-indicator" \
  "$path/vineyard-launcher" \
1>/dev/null
xgettext --from-code utf-8 -k_ -kN_ -o "$path/po/vineyard.pot" \
  "$path/vineyard/"*.py \
  "$path/data/vineyard-nautilus-infobar.py" \
  "$path/data/vineyard-nautilus-property-page.py" \
  "$path/data/vineyard-preferences.glade.h" \
1>/dev/null
rm "$path/data/vineyard-preferences.glade.h"
echo " done."

echo -n "Merging newly extracted strings with previous translations..."
for i in "$path/po/"*.po; do
	if [ -f "$i" ]; then
		msgmerge -U "$i" "$path/po/vineyard.pot" 1>/dev/null
	fi
done
echo " done."

echo -n "Compiling message catalogs to binary format..."
for i in "$path/po/"*.po; do
	language="$(basename $i | cut -d. -f1)"
	if [ ! -d "$path/data/locale/$language" ]; then
		mkdir -p "$path/data/locale/$language/LC_MESSAGES" 1>/dev/null
	fi
	msgfmt $i -o "$path/data/locale/$language/LC_MESSAGES/vineyard.mo" 1>/dev/null
done
echo " done."
