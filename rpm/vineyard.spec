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

%define srcname vineyard
%define version 0.1.6
%define build_timestamp %{lua: print(os.date("%Y%m%d"))}

Summary: Easy to use Wine configuration program and utility library
Name: %{srcname}
Version: %{version}
Release: %{build_timestamp}
Source0: https://github.com/Cybolic/vineyard/archive/master.zip#/%{srcname}-%{version}-%{release}.tar.gz
License: GPLv2+
BuildRequires: python2-devel
BuildArch: noarch
Vendor: Christian Dannie Storgaard <cybolic@gmail.com>
%{?python_provide:%python_provide python-wine}
Requires: (wine or wine-staging)
Requires: cabextract
Requires: winetricks
Requires: unzip
Requires: pygtk2
Requires: pygtk2-libglade
Recommends: python2-dbus
Recommends: mallard-rng
Recommends: nautilus-python
Url: https://github.com/Cybolic/vineyard

%description

Vineyard is a user friendly configuration tool for Wine that offers all the
features of winecfg (with the exception of the unfinished theme-support) as
well as bottle-handling and program-management in an easy to use program
designed to blend in with the GNOME desktop.

%prep
%autosetup -n %{srcname}-master

%build
# python setup.py build
%py2_build

%install
%py2_install
mkdir -p ${RPM_BUILD_ROOT}%{_datadir}/nautilus-python
# rpmlint will complain if we write the library path normally, hence the [i]
mv ${RPM_BUILD_ROOT}/usr/l[i]b/nautilus/extensions-2.0 ${RPM_BUILD_ROOT}%{_datadir}/nautilus-python/extensions

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%license COPYING
%doc README.md
%docdir %{_datadir}/vineyard/docs
%{python2_sitelib}/*
%{_bindir}/vineyard*
%{_datadir}/vineyard
%{_datadir}/applications
%{_datadir}/icons
%{_sysconfdir}/xdg/autostart
%{_datadir}/man
%{_datadir}/nautilus-python/extensions

%changelog

* Tue Dec 5 2017 - 0.1.6: Christian Dannie Storgaard <cybolic@gmail.com>
- Spec updated to work better in regards to outdated packages

* Sat Dec 2 2017 - 0.1.6: Christian Dannie Storgaard <cybolic@gmail.com>
- Initial spec file and RPM package
- This will be available in Fedora COPR, updated in sync with master
  - https://copr.fedorainfracloud.org/coprs/cybolic/Vineyard/
