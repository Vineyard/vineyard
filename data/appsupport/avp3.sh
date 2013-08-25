#!/bin/bash

# Create configuration and install support libraries
CREATE_CONFIGURATION 'Alien vs. Predator 3'
RUN 'winetricks d3dx9 d3dx10 physx vcrun2005'

# Install the game
WINE 'CDROM:\install.exe'

# Stop running dxdllreg.exe on startup (it doesn't work anyway, and doesn't seem to be needed)
SET_REGISTRY 'HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\dxregsvc' 'Start' 'dword:00000003'

# Find and run the game
if [ -f $(WIN_TO_UNIX 'C:\%ProgramFiles%\Aliens vs. Predator\AvP.exe') ]; then
    WINE 'C:\%ProgramFiles%\Aliens vs. Predator\AvP.exe'
elif [ -f $(WIN_TO_UNIX 'C:\~\Aliens vs. Predator\AvP.exe') ]; then
    WINE 'C:\~\Aliens vs. Predator\AvP.exe'
else
    cat <<ERRORMESSAGE
VINEYARD ERROR: Couldn't find the installed game.
If the installer completed successfully, then please start the game manually.
ERRORMESSAGE
fi


