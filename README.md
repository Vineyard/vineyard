# Vineyard

[![Build Status](https://travis-ci.org/Cybolic/vineyard.svg?branch=master)](https://travis-ci.org/Cybolic/vineyard)
![rpmbuild](https://copr.fedorainfracloud.org/coprs/cybolic/Vineyard/package/Git/status_image/last_build.png)

## Easy to use Wine configuration programs and libraries

Libraries and graphical utilities for using and configuring Wine from the Gnome desktop.
Incorporates many of the ideas found at [the Ubuntu Wiki](https://wiki.ubuntu.com/karmic-wine-integration).

If you would like to learn more about how it works, please visit the [project website](http://vineyardproject.org).

### Distribution Packages

If you would like to install in Ubuntu/Debian, you can use [the PPA](https://code.launchpad.net/~cybolic/+archive/ubuntu/ppa):

```bash
sudo add-apt-repository ppa:cybolic/vineyard-testing
sudo apt update
sudo apt install vineyard
```

To install in Fedora, you can use the COPR [respository](https://copr.fedorainfracloud.org/coprs/cybolic/Vineyard/):

```bash
sudo dnf copr enable cybolic/Vineyard
sudo dnf install vineyard
```

Vineyard is also [available in the Aurch User Repository (AUR)](https://aur.archlinux.org/packages/vineyard-git/).

### Install From Source

If you would like to help test the development version of Vineyard, please open a terminal and write:

```bash
sudo apt install git
git clone git@github.com:Cybolic/vineyard.git
```

To run this development version, use these commands (this will open Vineyard Preferences):

```bash
cd vineyard
./vineyard-preferences
```

Please report any errors, problems, thoughts or ideas you have concerning Vineyard [here on GitHub](https://github.com/Cybolic/vineyard/issues).
