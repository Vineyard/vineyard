#!/bin/bash

# Create configuration and install support libraries
CREATE_CONFIGURATION 'Torchlight'
INSTALL'dcom98 vcrun2008 mono24'

# Install the game
WINE 'CDROM:\Torchlight_Setup.exe'

# Setup the screen resolution
echo "VINEYARD INFO: Please select an appropriate game resolution and select ok.\nNote that the game will exit at that point, this is normal."
WINE 'C:\{Program Files}\Runic Games\Torchlight\Torchlight.exe' SAFEMODE=1
SET_VIRTUAL_DESKTOP --text "Now select the same resolution:"

# Run the game
WINE 'C:\{Program Files}\Runic Games\Torchlight\Torchlight.exe'
