# Vineyard

[![Build Status](https://travis-ci.org/Cybolic/vineyard.svg?branch=master)](https://travis-ci.org/Cybolic/vineyard)

## Easy to use Wine configuration programs and libraries

Libraries and graphical utilities for using and configuring Wine from the Gnome desktop.
Incorporates many of the ideas found at https://wiki.ubuntu.com/karmic-wine-integration.

If you would like to learn more about how it works, please visit the website:
http://vineyardproject.org

If you would like to install in Ubuntu/Debian, you can use [the PPA](https://code.launchpad.net/~cybolic/+archive/ubuntu/ppa):
```bash
sudo add-apt-repository ppa:cybolic/ppa
sudo apt update
sudo apt install vineyard```

If you would like to help test the development version of Vineyard in Ubuntu/Debian, you can use [the daily built PPA](https://code.launchpad.net/~cybolic/+archive/ubuntu/vineyard-testing):
```bash
sudo add-apt-repository ppa:cybolic/vineyard-testing
sudo apt update
sudo apt install vineyard```

Vineyard is also [available in the Aurch User Repository (AUR)](https://aur.archlinux.org/packages/vineyard-git/).

If you would like to help test the development version of Vineyard from trunk, please open a terminal and write:
```bash
sudo apt install git
git clone git@github.com:Cybolic/vineyard.git
```

To actually run this development version, use these commands (this will open Vineyard Preferences):
```bash
cd vineyard
./vineyard-preferences
```

Please report any errors, problems, thoughts or ideas you have concerning Vineyard either here at [GitHub](https://github.com/Cybolic/vineyard/issues) or at [Launchpad](https://bugs.launchpad.net/vineyard).
