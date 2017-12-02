#### NOTE: if building locally you may need to do the following:
####
#### yum install rpmdevtools -y
#### spectool -g -R rpm/quads.spec
####
#### At this point you can use rpmbuild -ba quads.spec
#### (this is because our Source0 is a remote Github location
####
#### Our upstream repository is located here:
#### https://copr.fedorainfracloud.org/coprs/cybolic/Vineyard

%define name vineyard
%define version 0.1.6
%define build_timestamp %{lua: print(os.date("%Y%m%d"))}

Summary: Easy to use Wine configuration program and utility library
Name: %{name}
Version: %{version}
Release: %{build_timestamp}
Source0: https://github.com/Cybolic/vineyard/archive/master.zip#/%{name}-%{version}-%{release}.tar.gz
License: GPLv2+
BuildRoot: %{_tmppath}/%{name}-buildroot
BuildArch: noarch
Vendor: Christian Dannie Storgaard <cybolic@gmail.com>
Requires: (wine or wine-staging)
Requires: cabextract
Requires: winetricks
Requires: unzip
Requires: python >= 2.4
Requires: python-glade2
Requires: python-dbus
Requires: python-appindicator
Url: https://github.com/Cybolic/vineyard

%description

Vineyard is a user friendly configuration tool for Wine that offers all the
features of winecfg (with the exception of the unfinished theme-support) as
well as bottle-handling and program-management in an easy to use program
designed to blend in with the GNOME desktop.

%prep
%autosetup -n %{name}-master

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/

%changelog

* Sat Dec 2 2017 - 0.1.6: Christian Dannie Storgaard <cybolic@gmail.com>
- Initial spec file and RPM package
- This will be available in Fedora COPR, updated in sync with master
  - https://copr.fedorainfracloud.org/coprs/cybolic/Vineyard/
