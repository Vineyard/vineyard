#!/bin/bash

# Exit at any command failure
set -e
# Exit if any unused variable is attempted used
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")//..//" && echo $PWD)"
echo $SCRIPT_DIR
VINEYARD_CLI="$(which vineyard-cli || echo "")"
echo "$SCRIPT_DIR/vineyard-cli"
if [ -z $VINEYARD_CLI ]; then
	if [ -x "$SCRIPT_DIR/vineyard-cli" ]; then
		VINEYARD_CLI="$SCRIPT_DIR/vineyard-cli"
	elif [ -x "$SCRIPT_DIR/../vineyard-cli" ]; then
		VINEYARD_CLI="$SCRIPT_DIR/../vineyard-cli"
	else
		echo "Couldn't find vineyard-cli, exiting."
		exit 1
	fi
fi

CONFIGURATION_DIR="$HOME"
PYTHON_WINE_START='import sys, os; sys.path.insert(0, '"'%s/python-wine'"' % os.path.abspath(os.path.dirname(sys.argv[0]))); import wine; '

function CREATE_CONFIGURATION() {
    if [ -z "$OVERRIDE_CONFIGURATION_NAME" ]; then
        CONFIGURATION_NAME="$1"
    else
        CONFIGURATION_NAME="$OVERRIDE_CONFIGURATION_NAME"
    fi
    $VINEYARD_CLI --add-conf "$CONFIGURATION_NAME"
    
    CONFIGURATION_DIR="$($VINEYARD_CLI --list-confs | grep "$CONF_NAME")"
    CONFIGURATION_DIR="$(echo $CONFIGURATION_DIR | grep -E --color=never -o '/home/.*/\..*')"
}

function USE_CONFIGURATION() {
    CONFIGURATION_NAME="$1"
    $VINEYARD_CLI --use-conf "$CONFIGURATION_NAME"
    
    CONFIGURATION_DIR="$($VINEYARD_CLI --list-confs | grep "$CONF_NAME")"
    CONFIGURATION_DIR="$(echo $CONFIGURATION_DIR | grep -E --color=never -o '/home/.*/\..*')"
}

function RUN() {
    $VINEYARD_CLI --use-conf "$CONFIGURATION_NAME" --run "$@"
}

function INSTALL() {
    $VINEYARD_CLI --use-conf "$CONFIGURATION_NAME" --run "install $1"
}

function SET_REGISTRY() {
    $VINEYARD_CLI --set-registry "$@"
}

function SET_OVERRIDE() {
    python -c "$PYTHON_WINE_START"' wine.libraries.set_override(sys.argv[1], sys.argv[2])' "$1" "$2" 
}

function SET_VERSION() {
	python -c "$PYTHON_WINE_START"' wine.prefixes.use("'$CONFIGURATION_NAME'"); wine.version.set(sys.argv[1])' "$@"
}

function WINE() {
    env WINEPREFIX="$CONFIGURATION_DIR/.wine" HOME="$CONFIGURATION_DIR" wine "$@"
}

function REGEDIT() {
    env WINEPREFIX="$CONFIGURATION_DIR/.wine" HOME="$CONFIGURATION_DIR" wine regedit "$@"
}

function WIN_TO_UNIX() {
	python -c "$PYTHON_WINE_START"' wine.prefixes.use("$CONFIGURATION_NAME"); print wine.util.wintounix(sys.argv[1])' "$@"
}

function UNIX_TO_WIN() {
	python -c "$PYTHON_WINE_START"' wine.prefixes.use("$CONFIGURATION_NAME"); print wine.util.unixtowin(sys.argv[1])' "$@"
}

function NOTIFY_OF_DRM() {
	# Pop up a dialog with the following:
	# "This game or program is known to use copy-protection or Digital Rights Management."
	# "Due to legality issues, this cannot be supported directly."
	# "You might be able to run the game by applying an unofficial patch (often called a NoCD patch or crack)."
	# "Again, this is a legal grey area, but you may have luck searching for it on the internet."
}

echo "Done"

echo "$(WIN_TO_UNIX "%ProgramFiles%/Star Craft 2")"
SET_OVERRIDE "multidllfiletest" "builtin,   native"
WINE winecfg