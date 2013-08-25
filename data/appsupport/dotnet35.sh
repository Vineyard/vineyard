#!/bin/bash

# First install previous versions of .NET
# As suggested here: http://appdb.winehq.org/objectManager.php?sClass=version&iId=10166&iTestingId=25041
INSTALL dotnet20
INSTALL dotnet30

# Download the installer
# FIXME: Figure out best argument support
DOWNLOAD_FROM_SITE 'http://DONT KNOW WHERE!' \
'<td>HTTP</td><td><a href="(.*?\.exe)"' \
'dotnet35.exe'

# 

# Install the game
WINE "$PATH_TO_WHERE_WE_PUT_DOWNLOADS\dotnet35.exe"