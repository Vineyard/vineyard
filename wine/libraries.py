#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import common
import registry, drives
import os, sys

PACKAGES = {
    #"Microsoft Visual Basic 6 Runtime": ('asycfilt.dll', 'comcat.dll', 'msvbvm60.dll', 'oleaut32.dll', 'olepro32.dll', 'stdole2.tlb', 'advpack.dll', 'vbrun60.inf', 'w95inf16.dll', 'w95inf32.dll'),
    'vb6run': ('asycfilt.dll', 'comcat.dll', 'msvbvm60.dll', 'oleaut32.dll', 'olepro32.dll', 'stdole2.tlb', 'advpack.dll', 'vbrun60.inf', 'w95inf16.dll', 'w95inf32.dll'),
    #"Microsoft Visual Basic 5 Runtime": ('msvbvm50.dll', 'oleaut32.dll', 'olepro32.dll', 'stdole2.tlb', 'asycfilt.dll', 'comcat.dll'),
    'vb5run': ('msvbvm50.dll', 'oleaut32.dll', 'olepro32.dll', 'stdole2.tlb', 'asycfilt.dll', 'comcat.dll'),
    #"Microsoft Visual Basic 4 Runtime": ('vb40016.dll', 'vb40032.dll'),
    'vb4run': ('vb40016.dll', 'vb40032.dll'),
    #"Microsoft Visual Basic 3 Runtime": ('vbrun300.dll'),
    'vb3run': ('vbrun300.dll'),
    #"Microsoft Visual C++ 2010": ('mfc100.dll', 'msvcp100.dll' , 'msvcr100.dll'),
    'vcrun2010': ('mfc100.dll', 'msvcp100.dll' , 'msvcr100.dll'),
    #"Microsoft Visual C++ 2008": ('mfc90.dll', 'msvcr90.dll', 'msvcp90.dll', 'msvcr90d.dll', 'msvcp90d.dll'),
    'vcrun2008': ('mfc90.dll', 'msvcr90.dll', 'msvcp90.dll', 'msvcr90d.dll', 'msvcp90d.dll'),
    #"Microsoft Visual C++ 2005": ('mfc80.dll', 'msvcr80.dll', 'msvcp80.dll', 'msvcr80d.dll', 'msvcp80d.dll'),
    'vcrun2005': ('mfc80.dll', 'msvcr80.dll', 'msvcp80.dll', 'msvcr80d.dll', 'msvcp80d.dll'),
    #"Microsoft Visual C++ 2003": ('mfc71.dll', 'msvcr71.dll', 'msvcp71.dll', 'msvcr71d.dll', 'msvcp71d.dll'),
    'vcrun6': ('mfc71.dll', 'msvcr71.dll', 'msvcp71.dll', 'msvcr71d.dll', 'msvcp71d.dll'),
    #"Microsoft Visual C++ 2002": ('mfc71.dll', 'msvcr70.dll', 'msvcp70.dll', 'msvcr70d.dll', 'msvcp70d.dll'),
    'vcrun2002': ('mfc71.dll', 'msvcr70.dll', 'msvcp70.dll', 'msvcr70d.dll', 'msvcp70d.dll'),
    #"Microsoft Visual C++ 6.0": ('mfc42.dll', 'msvcrt.dll', 'msvcp60.dll', 'msvcrtd.dll', 'msvcp60d.dll'),
    "Microsoft Visual C++ 6.0": ('mfc42.dll', 'msvcrt.dll', 'msvcp60.dll', 'msvcrtd.dll', 'msvcp60d.dll'),
    #"Microsoft Visual C++ 5.0": ('mfc.dll', 'msvcrt.dll', 'msvcp50.dll', 'msvcrtd.dll', 'msvcp50d.dll'),
    "Microsoft Visual C++ 5.0": ('mfc.dll', 'msvcrt.dll', 'msvcp50.dll', 'msvcrtd.dll', 'msvcp50d.dll'),
    #"Microsoft Visual C++ 4.2": ('mfc.dll', 'msvcrt.dll', 'msvcrtd.dll', 'msvcprt.lib', 'msvcprtd.lib'),
    "Microsoft Visual C++ 4.2": ('mfc.dll', 'msvcrt.dll', 'msvcrtd.dll', 'msvcprt.lib', 'msvcprtd.lib'),
    #"Windows Media Player": ('blackbox.dll', 'cewmdm.dll', 'drmclien.dll', 'drmstor.dll', 'drmv2clt.dll', 'laprxy.dll',
    "Windows Media Player": ('blackbox.dll', 'cewmdm.dll', 'drmclien.dll', 'drmstor.dll', 'drmv2clt.dll', 'laprxy.dll',
        'mp43dmod.dll', 'mp4sdmod.dll', 'mpg4dmod.dll', 'msdmo.dll', 'msnetobj.dll', 'mspmsnsv.dll', 'mspmsp.dll',
        'msscp.dll', 'mswmdm.dll', 'npdrmv2.dll', 'npwmsdrm.dll', 'qasf.dll', 'wdfapi.dll', 'wmadmod.dll', 'wmadmoe.dll',
        'wmasf.dll', 'wmdmlog.dll', 'wmdmps.dll', 'wmdrmdev.dll', 'wmdrmnet.dll', 'wmidx.dll', 'wmnetmgr.dll', 'wmsdmod.dll',
        'wmsdmoe2.dll', 'wmspdmod.dll', 'wmspdmoe.dll', 'wmvadvd.dll', 'wmvadve.dll', 'wmvcore.dll', 'wmvdmod.dll',
        'wmvdmoe2.dll', 'wpd_ci.dll', 'wpdconns.dll', 'wpdmtp.dll', 'wpdmtpdr.dll', 'wpdmtpus.dll', 'wpdsp.dll', 'wpdtrace.dll'
    ),
    "MS XACT Engine": ('xactengine*.dll', 'xaudio*.dll'),
    'Direct3D': ('d3dx9_43.dll')
}
BUILTIN = ("advapi32", "capi2032", "dbghelp", "ddraw", "gdi32", "glu32", "icmp", "gphoto2.ds", "iphlpapi", "kernel32",
    "mountmgr.sys", "mswsock", "ntdll", "ntoskrnl.exe", "opengl32", "sane.ds", "twain_32", "unicows", "user32", "vdmdbg",
    "w32skrnl", "winealsa.drv", "wineaudioio.drv", "wined3d", "winedos", "wineesd.drv", "winejack.drv", "winejoystick.drv",
    "winemp3.acm", "winenas.drv", "wineoss.drv", "wineps", "wineps.drv", "winex11.drv", "winmm", "wintab32", "wnaspi32",
    "wow32", "ws2_32", "wsock32")

def list():
    library_paths =  common.ENV.get('WINEDLLPATH', '').split(':')
    library_paths += [ i+'/wine' for i in common.ENV.get('LD_LIBRARY_PATH', '').split(':') ]
    library_paths += [
        "/usr/local/lib/wine", "/usr/lib/wine",
        "/usr/lib/i386-linux-gnu/wine/", "/usr/local/lib/i386-linux-gnu/wine/",
        "/usr/lib/x86_64-linux-gnu/wine/", "/usr/local/lib/x86_64-linux-gnu/wine/",
        "/usr/lib32/wine", "/usr/local/lib32/wine",
        "/usr/lib64/wine", "/usr/local/lib64/wine"
    ]
    # Remove duplicates whilst preserving order (unlike set())
    library_paths = [ library_paths[i] for i,v in enumerate(library_paths) if v not in library_paths[i+1:]]

    libs = []
    for libpath in library_paths:
        if os.path.exists(libpath):
            print "\tIt exists, adding..."+libpath
            libs += [ i[:-7] for i in filter(lambda i: i.endswith(".dll.so"), os.listdir(libpath)) ]

    libraries = []
    for lib in set(libs):
        if lib not in BUILTIN:
            libraries.append(lib)

    return sorted(libraries)


#@common.read_cache('libraries-overrides')
def get_overrides():
    libs = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\DllOverrides', quiet=True)
    overridden = []
    for lib, setting in libs.iteritems():
        if not setting.startswith("builtin"):
            overridden.append( (lib, setting) )
    return sorted(overridden)

@common.clear_cache('libraries-overrides')
def set_override(library, override):
    _override = override
    if library.endswith(".dll"):
        library = library[:-4]
    if type(override) is bool:
        if override:
            registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DllOverrides': {
                library: "native,builtin"}})
        else:
            registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DllOverrides': {
                library: None}})
    else:
        if type(override) is str:
            override = override.lower()

            if override.startswith('disable'):
                override = ''
            else:
                # make sure that the override is separated by only commas
                override = ','.join([
                    i.strip() for i
                    in filter(len, override.replace(',', ' ').split())
                ])

        if library.lower() == 'comctl32':
            common.run([
                'rm', '-rf', util.wintounix(
                    "{0}\\windows\\winsxs\\manifests\\"+
                    "x86_microsoft.windows."+
                    "common-controls_6595b64144ccf1df_6.0."+
                    "2600.2982_none_deadbeef.manifest".format(
                        drives.get_main_drive(use_registry=False)
                    )
                )
            ])

        if override in ('native', 'builtin',
                         'native,builtin', 'builtin,native',
                         '', 'disabled', None):
            registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DllOverrides': {
                library: override}})
        else:
            raise ValueError("Wrong value for override: {0}".format(_override))

