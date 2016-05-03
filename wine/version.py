#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import common, registry

# wine/programs/winecfg/appdefaults.c
DEFAULT = 'winxp'
windowsversions_sorted = common.sorteddict(

    ("win10", [
        "Windows 10",       10,  0, 0x2800,"WIN32_NT", " ", 0, 0, "WinNT"]),
    ("win81", [
        "Windows 8.1",       6,  3, 0x2580,"WIN32_NT", " ", 0, 0, "WinNT"]),
    ("win8", [
        "Windows 8",         6,  2, 0x23F0,"WIN32_NT", " ", 0, 0, "WinNT"]),
    ("win2008r2", [
        "Windows 2008 R2",   6,  1, 0x1DB1,"WIN32_NT", "Service Pack 1", 1, 0, "ServerNT"]),
    ("win7", [
        "Windows 7",         6,  1, 0x1DB1,"WIN32_NT", "Service Pack 1", 1, 0, "WinNT"]),
    ("win2008", [
        "Windows 2008",      6,  0, 0x1772,"WIN32_NT", "Service Pack 2", 2, 0, "ServerNT"]),
    ("vista", [
        "Windows Vista",     6,  0, 0x1772,"WIN32_NT", "Service Pack 2", 2, 0, "WinNT"]),
    ("win2003", [
        "Windows 2003",      5,  2, 0xECE, "WIN32_NT", "Service Pack 2", 2, 0, "ServerNT"]),

    ("winxp64", [
        "Windows XP",        5,  2, 0xECE, "WIN32_NT", "Service Pack 2", 2, 0, "WinNT"]),

    ("winxp", [
        "Windows XP",        5,  1, 0xA28, "WIN32_NT", "Service Pack 3", 3, 0, "WinNT"]),
    ("win2k", [
        "Windows 2000",      5,  0, 0x893, "WIN32_NT", "Service Pack 4", 4, 0, "WinNT"]),
    ("winme", [
        "Windows ME",        4, 90, 0xBB8, "WIN32_WINDOWS", " ", 0, 0, ""]),
    ("win98", [
        "Windows 98",        4, 10, 0x8AE, "WIN32_WINDOWS", " A ", 0, 0, ""]),
    ("win95", [
        "Windows 95",        4,  0, 0x3B6, "WIN32_WINDOWS", "", 0, 0, ""]),
    ("nt40", [
        "Windows NT 4.0",    4,  0, 0x565, "WIN32_NT", "Service Pack 6a", 6, 0, "WinNT"]),
    ("nt351", [
        "Windows NT 3.51",   3, 51, 0x421, "WIN32_NT", "Service Pack 5", 5, 0, "WinNT"]),
    ("win31", [
        "Windows 3.1",       3, 10,     0, "WIN32S", "Win32s 1.3", 0, 0, ""]),
    ("win30", [
        "Windows 3.0",       3,  0,     0, "WIN32S", "Win32s 1.3", 0, 0, ""]),
    ("win20", [
        "Windows 2.0",       2,  0,     0, "WIN32S", "Win32s 1.3", 0, 0, ""])
)
windowsversions = windowsversions_sorted.dict()
versions = [ i for i in reversed(windowsversions_sorted.keys()) ]
wDescription = 0
wMajorVersion = 1
wMinorVersion = 2
wBuildNumber = 3
wPlatformId = 4
wCSDVersion = 5
wServicePackMajor = 6
wServicePackMinor = 7
wProductType = 8
Key9x = "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion"
KeyNT = "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion"
KeyProdNT = "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\ProductOptions"
KeyWindNT = "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Windows"
KeyEnvNT  = "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\Session Manager\\Environment"


def get(program=None):
    if program:
        version = None
        programs = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults', quiet=True)
        for key in programs.keys():
            programs[key.lower()] = programs[key]
        if program.lower() in programs.keys() and 'Version' in programs[program.lower()]:
            version = programs[program.lower()]['Version']
        if version == None or version not in windowsversions.keys():
            return DEFAULT
        else:
            return version
    else:
        version = registry.get('HKEY_CURRENT_USER\\Software\\Wine', "Version", quiet=True)
        if version:
            if version == None or version not in windowsversions.keys():
                return DEFAULT
            else:
                return version
        else:
            return _parseWineVersionFromRegistry()

def set(version, program=False):
    version = __translate_version_string(version)
    if version not in versions:
        raise KeyError(
            "Error: Version should be one of the following: default, {0}".format(
                ", ".join(versions)
            )
        )

    if program:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s' % program: {"Version": version} })
    else:
        set_default(version)

def set_default(version):
    version = __translate_version_string(version, strict=True)
    shortversion = version
    version = windowsversions[version]

    # Clear values first
    registry_values = {
        Key9x: { "VersionNumber": None, "SubVersionNumber": None },
        KeyNT: { "CSDVersion": None, "CurrentVersion": None, "CurrentBuildNumber": None },
        KeyProdNT: { "ProductType": None },
        KeyWindNT: { "CSDVersion": None },
        KeyEnvNT: { "OS": None },
        'HKEY_LOCAL_MACHINE\\System\\CurrentControlSet\\Control\\ServiceCurrent': { "OS": None },
        'HKEY_CURRENT_USER\\Software\\Wine': { "Version": None }
    }

    # Set the required keys for the tree types of version info that exist so far
    if version[wPlatformId] == "WIN32_WINDOWS":
        registry_values.update({
            Key9x: {
                "VersionNumber": "{0}.{1}.{2}".format(
                    version[wMajorVersion], version[wMinorVersion], version[wBuildNumber]
                ),
                "SubVersionNumber": version[wCSDVersion]
            }
        })

    elif version[wPlatformId] == "WIN32_NT":
        registry_values.update({
            KeyNT: {
                "CurrentVersion": "{0}.{1}".format(
                    version[wMajorVersion], version[wMinorVersion]
                ),
                "CSDVersion": version[wCSDVersion],
                "CurrentBuildNumber": version[wBuildNumber]
            },
            KeyProdNT: { "ProductType": version[wProductType] },
            KeyWindNT: { "CSDVersion": "dword:00000%s00" % version[wServicePackMajor] },
            KeyEnvNT: { "OS": "Windows_NT" }
        })

    elif version[wPlatformId] == "WIN32s":
        registry_values.update({
            'HKEY_CURRENT_USER\\Software\\Wine': {"Version": shortversion}
        })

    registry.set(registry_values)

def _parseWineVersionFromRegistry():
    # Note, good info here as well, though it's a bit too precise for what we
    # need for Wine... but you never know ;)
    # http://techsupt.winbatch.com/TS/T000001074F4.html
    versionnt = registry.get(KeyNT, "CurrentVersion")
    version9x = registry.get(Key9x, "VersionNumber")
    best = DEFAULT # hardcoded fallback (same as in winecfg)

    if versionnt:
        version = versionnt
        platform = "WIN32_NT"
        build = int(registry.get(KeyNT, "CurrentBuildNumber"))
    elif version9x:
        version = version9x
        platform = "WIN32_WINDOWS"
    else:
        return best

    # Strip non-legal characters, if needed
    try:
        int(version)
    except ValueError:
        chars = '0123456789.'
        version = ''.join(( i for i in version if i in chars ))

    if '.' in version:
        parts = version.split('.')
        if len(parts) == 3:
            build = int(parts[2])
        minor = int(parts[1])
        major = int(parts[0])
    else:
        major = int(version)

    for winver,data in windowsversions.iteritems():
        if data[wPlatformId] != platform or data[wMajorVersion] != major:
            continue
        best = winver
        if data[wMinorVersion] == minor and data[wBuildNumber] == build:
            return winver
    return best

def get_programs():
    programs = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults', quiet=True)
    for key in programs.keys():
        programs[key.lower()] = programs[key]
    return programs

def __translate_version_string(version, strict=False):
    version = version.lower()
    if version == "default":
        return DEFAULT
    elif version == "win2000":
        return "win2k"
    return version
