#!/bin/sh

dir="$(basename "$(readlink -f "$(dirname "$0")/../")")"
path="$(readlink -f "$(dirname "$0")/../../")"

version="$(head "$path/$dir/debian/changelog" -n 1 | cut -d\( -f2 | cut -d\) -f1)"
sourceversion="$(echo $version | cut -d- -f1 | cut -d\~ -f1)"

pod2man --section=1 --release=$sourceversion --center="Windows On Unix" "$path/$dir/data/vineyard-preferences.pod" > "$path/$dir/data/vineyard-preferences.1"
gzip -9 "$path/$dir/data/vineyard-preferences.1"
