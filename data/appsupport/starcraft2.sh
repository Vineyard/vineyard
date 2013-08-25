#!/bin/bash

# If install from CD
sudo umount /media/SC2*
sudo mkdir /media/cdrom
sudo mount -t udf -o ro,unhide,uid=$(id -u) /dev/cdrom /media/cdrom

INSTALL droid fontfix fontsmooth-rgb gdiplus gecko vcrun2008 vcrun2005 allfonts d3dx9 win7
SET-OVERRIDE mmdevapi disabled
SET-REGISTRY 'HKEY_CURRENT_USER\Software\Wine\Direct3D\UseGLSL' 'disabled'

RUN 'D:\installer.exe'
