#!/bin/bash

# Download the installer
# FIXME: Figure out best argument support
DOWNLOAD_FROM_SITE 'http://www.codecguide.com/download_k-lite_codec_pack_mega.htm' \
'<td>HTTP</td><td><a href="(.*?\.exe)"' \
'K-Lite_Codec_Pack_Mega.exe'

# Install the game
WINE 'D:\Torchlight_Setup.exe'

# Setup the screen resolution
echo "VINEYARD INFO: Please select an appropriate game resolution and select ok.\nNote that the game will exit at that point, this is normal."
WINE 'C:\{Program Files}\Runic Games\Torchlight\Torchlight.exe' SAFEMODE=1
SET_VIRTUAL_DESKTOP --text "Now select the same resolution:"

# Run the game
WINE 'C:\{Program Files}\Runic Games\Torchlight\Torchlight.exe'
