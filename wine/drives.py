#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import registry, util, common, command
import os, subprocess, re, string

DRIVE_TYPES = ['hd', 'network', 'cdrom', 'floppy']
SUPPORTED_IMAGE_FORMATS = ('iso', 'bin', 'nrg', 'img', 'mdf')

def drive_mapping_to_reg(driveletter, mapping):
    hexmapping = util.utf8tohex(mapping).upper()
    hexletter = "00000000-0000-0000-0000-0000000000%s" % driveletter.upper().encode('hex')

    registry.set({'HKEY_LOCAL_MACHINE\\System\\MountedDevices': {
        "\\\\??\\\\Volume{%s}" % hexletter: "hex:%s" % hexmapping,
        "\\\\DosDevices\\\\%s:" % driveletter.upper(): "hex:%s" % hexmapping
    }})
    registry.set({'HKEY_LOCAL_MACHINE\\Software\\Wine\\Drives': {
        "%s:" % driveletter.upper(): "hd"
    }})

def get_main_drive(drives=None, use_registry=True):
    if drives == None:
        drives = get(use_registry=use_registry)
    if len(drives.keys()):
        return drives[ sorted(drives.keys())[0] ]
    else:
        return 

def add(driveletter, mapping, label=None, serial=None, drive_type=None, device_file=None):
    """Add a new drive or update an existing one."""
    driveletter = driveletter.lower()[0]
    drivemapping = os.path.normpath(
        "%s/dosdevices/%s:" % (common.ENV['WINEPREFIX'], driveletter)
    )
    mapping = os.path.normpath(mapping)
    if mapping.startswith(common.ENV['WINEPREFIX']):
        mapping = os.path.relpath(mapping, '%s/dosdevices' % common.ENV['WINEPREFIX'])

    # If the directory does not already exist and is a link that is already
    # set to what we need.
    # IE: If the mapping is different from what was requested.
    if not (
        os.path.lexists(drivemapping) and
        os.path.islink(drivemapping) and
        os.path.realpath(drivemapping) == os.path.realpath(mapping)
    ):
        #print drivemapping
        # Else set up the mapping
        if os.path.lexists(drivemapping) and os.path.islink(drivemapping):
            os.remove(drivemapping)

        os.symlink(mapping, drivemapping)

    drive_mapping_to_reg(driveletter, mapping)

    returncode = subprocess.call(["wine", "net", "stop", "mountmgr"], env=common.ENV)
    returncode = subprocess.call(["wine", "net", "start", "mountmgr"], env=common.ENV)

    # If label or serial is given
    try:
        if type != 'cdrom':    # Don't try writing to read-only media
            if label == None:
                os.remove("%s/.windows-label" % drivemapping)
            else:
                with open("%s/.windows-label" % drivemapping, 'w') as label_file:
                    label_file.write("{0}\n".format(label))

            if serial == None:
                os.remove("%s/.windows-serial" % drivemapping)
            else:
                with open("%s/.windows-serial" % drivemapping, 'w') as serial_file:
                    serial_file.write("{0}\n".format(serial))
    except (IOError, OSError):
        # This probably a read-only device, no worry
        pass

    if drive_type is not None:
        set_type(driveletter, drive_type)

    if device_file is not None:
        set_device(driveletter, device_file)

def remove(driveletter):
    driveletter = driveletter[0]
    for driverletter_case in (driveletter.upper(), driveletter.lower()):
        drive_path = '{wineprefix}/dosdevices/{drive}:'.format(
            wineprefix = common.ENV['WINEPREFIX'],
            drive = driverletter_case
        )
        drive_device_path = '{0}:'.format(drive_path)

        if os.path.lexists(drive_path):
            os.remove(drive_path)
        if os.path.lexists(drive_device_path):
            os.remove(drive_device_path)

    registry.set({'HKEY_LOCAL_MACHINE\\Software\\Wine\\Drives': {
        "%s:" % driveletter: None
    }})

    hex_letter = '00000000-0000-0000-0000-0000000000{hex_letter}'.format(
        hex_letter = driveletter.upper().encode('hex')
    )
    registry.set({'HKEY_LOCAL_MACHINE\\System\\MountedDevices': {
        "\\\\??\\\\Volume{%s}" % hex_letter: None,
        "\\\\DosDevices\\\\%s:" % driveletter.upper(): None
    }})
    registry.set({'HKEY_LOCAL_MACHINE\\System\\MountedDevices': {
        "\\??\\Volume{%s}" % hex_letter: None,
        "\\DosDevices\\%s:" % driveletter.upper(): None
    }})


def set_type(driveletter, drive_type):
    # Make sure we use the same caps for the driveletter as the reg
    typesraw = registry.get('HKEY_LOCAL_MACHINE\\Software\\Wine\\Drives', quiet=True, shallow=True)
    for key,value in typesraw.iteritems():
        if key.lower == driveletter.lower():
            driverletter = key
    # Save it
    if drive_type not in DRIVE_TYPES or drive_type != None:
        util.warning("Setting drive type to unknown value: %s" % drive_type)
    registry.set({'HKEY_LOCAL_MACHINE\\Software\\Wine\\Drives': {"%s:" % driveletter: drive_type}})

def set_device(drive_letter, device_path):
    drive_letter = drive_letter[0]
    for driverletter_case in (drive_letter.upper(), drive_letter.lower()):
        symlink_path = '{wineprefix}/dosdevices/{drive}::'.format(
            wineprefix = common.ENV['WINEPREFIX'],
            drive = driverletter_case
        )

        if os.path.lexists(symlink_path):
            os.remove(symlink_path)

    # Now that all device symlinks are removed, let create the path for the new
    symlink_path = '{wineprefix}/dosdevices/{drive}::'.format(
        wineprefix = common.ENV['WINEPREFIX'],
        drive = drive_letter.lower()
    )

    os.symlink(device_path, symlink_path)
    auto_mount_image(device_path)


def auto_mount_image(device):
    """Mounts the mapping if it's an image file, else does nothing."""
    if device[-3:].lower() in SUPPORTED_IMAGE_FORMATS:
        return util.mount_iso(device)
    return device

def auto_mount_images():
    """Auto mount all image files."""

    for drive in os.listdir('%s/dosdevices' % common.ENV['WINEPREFIX']):
        if len(drive) > 2:
            continue
        drive = drive[0]
        device_path = get_internal_path_for_drive_device(drive)
        if device_path != None:
            device_path = os.path.realpath(device_path)
            #print "Trying to mount", device_path
            parsed_mapping = auto_mount_image(device_path)
            #print "Mounted on", parsed_mapping
            # Here we could test whether the parsed_mapping and the current
            # mapping matches, but let's give the user some room
            # to do fancy stuff (e.g. overriding image files)

def list(use_registry=True, basic=False):
    """
    Prints a list of drive mappings similar to:

    Drive:      C
    Mapping:    /home/user/.wine/drive_c
    Label:      Windows
    Serial:     0

    Label and Serial are only printed if they are set."""

    drives = get(use_registry=use_registry, basic=basic)

    _list = []
    for drive, info in drives.iteritems():
        _list.append( ['Drive:', '%s:' % drive.upper()] )
        _list.append( ['Mapping:', os.path.realpath(info['mapping'])] )

        for value in ['device', 'type', 'label', 'serial']:
            if value in info:
                _list.append( ['%s:' % value.capitalize(), info[value]] )
        _list.append([])

    return util.get_print_in_cols(_list[:-1])

def get(use_registry=True, basic=False):
    """
    Get a dictionary of the available drives for this configuration.
    Note that this might include less drives than winecfg will show since this
    functions will only include drives that are actually visible to programs,
    unlike winecfg."""
    drives = {}
    types = {}
    if use_registry:
        types_raw = registry.get('HKEY_LOCAL_MACHINE\\Software\\Wine\\Drives', shallow=True)
        util.dict_to_case_insensitive(types_raw)

    for drive in os.listdir('%s/dosdevices' % common.ENV['WINEPREFIX']):
        # Skip device links
        if drive.endswith('::'):
            continue
        # Skip non-drive links (eg. printers)
        if drive.endswith(':') == False:
            continue

        drive_letter = drive[0].upper()
        drives[drive_letter] = {}

        drive_path = get_internal_path_for_drive(drive)
        #print("Drive: %s\nDrive path: %s" % (drive, drive_path))
        drives[drive_letter]['mapping'] = os.path.realpath(drive_path)

        drive_device_path = get_internal_path_for_drive_device(drive)
        if drive_device_path != None:
            drives[drive_letter]['device'] = os.path.realpath(drive_device_path)

        if not basic:
            if os.path.exists("%s/.windows-label" % drive_path):
                f = open("%s/.windows-label" % drive_path)
                drives[drive_letter]['label'] = f.read().replace('\n','').replace('\r','')
                f.close()
            if os.path.exists("%s/.windows-serial" % drive_path):
                f = open("%s/.windows-serial" % drive_path)
                drives[drive_letter]['serial'] = f.read().replace('\n','').replace('\r','')
                f.close()
        if use_registry:
            if drive.lower() in types.keys():
                drives[drive_letter]['type'] = types[drive.lower()]
    return drives

def get_show_dot_files():
    if 'show-dot-files' in CACHE:
        return CACHE['show-dot-files']
    value = registry.get(
        'HKEY_CURRENT_USER\\Software\\Wine',
        'ShowDotFiles'
    ) in ('y', 'Y')
    CACHE['show-dot-files'] = value
    return value

def set_show_dot_files(value):
    if value:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine': {"ShowDotFiles": "Y"} })
        CACHE['show-dot-files'] = True
    else:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine': {"ShowDotFiles": "N"} })
        CACHE['show-dot-files'] = False

def get_auto_detect():
    # Remove existing drives (wine may complain)

    #for filename in os.listdir("%s/dosdevices/" % common.ENV['WINEPREFIX']):
    #    if filename.lower() != 'c:':
    #        os.remove("%s/dosdevices/%s" % (common.ENV['WINEPREFIX'], filename))
    #drives = registry.get('HKEY_LOCAL_MACHINE\\System\\MountedDevices')
    #typesraw = registry.get('HKEY_LOCAL_MACHINE\\Software\\Wine\\Drives')
    #for drive in drives.keys():
    #    if drive.lower() != '\\??\\volume{00000000-0000-0000-0000-000000000043}' and drive.lower() != '\dosdevices\c:':
    #        drives[drive] = None
    #for drive in typesraw.keys():
    #    if drive.lower != 'c:':
    #        typesraw[drive] = None
    #registry.set({'HKEY_LOCAL_MACHINE\\System\\MountedDevices': drives})
    #registry.set({'HKEY_LOCAL_MACHINE\\Software\\Wine\\Drives': typesraw})

    # Get drives
    drives = {
        'C:': {
            'mapping': '%s/drive_c' % common.ENV['WINEPREFIX'],
            'type': 'hd'
        },
        'Z:': {
            'mapping': "/",
            'type': 'hd'
        }
    }
    cdrom_device = get_system_info_cdrom()
    if cdrom_device is not None:
        drives['D:'] = {
            'type': 'cdrom',
            'device': cdrom_device
        }
        for path in [
            '/media/cdrom', '/media/cdrom0',
            '/mnt/cdrom', '/mnt/cdrom0'
        ]:
            if os.path.exists(path):
                drives['D:']['mapping'] = path
                break
        if 'mapping' not in drives['D:']:
            for path in ['/media', '/mnt']:
                if os.path.exists(path):
                    drives['D:']['mapping'] = '%s/cdrom' % path
                    break

    floppy_device = get_system_info_floppy()
    if floppy_device is not None:
        drives['A:'] = {
            'type': 'floppy',
            'device': floppy_device
        }
        for path in [
            '/media/floppy', '/media/floppy0',
            '/mnt/floppy', '/mnt/floppy0'
        ]:
            if os.path.exists(path):
                drives['A:']['mapping'] = path
                break
        if 'mapping' not in drives['D:']:
            for path in ['/media', '/mnt']:
                if os.path.exists(path):
                    drives['D:']['mapping'] = '%s/floppy' % path
                    break

    return drives

    # Add drives
    #for driveletter, mapping in drives.iteritems():
    #    self.add(driveletter, mapping)
    #    self.setType(driveletter, 'hd')
    #
    #if 'D' in drives:
    #    self.setType('D', 'cdrom')

def get_system_info_cdrom():
    if os.path.exists('/proc/sys/dev/cdrom/info'):
        location = util.get_command_output(('grep', 'drive name:', '/proc/sys/dev/cdrom/info'))
        location = '/dev/%s' % location.split("\t")[-1].strip()
        return location
    else:
        return None

def get_system_info_floppy():
    """ This is based on /var/log/dmesg files found on Google,
    but I don't own a floppy drive, so I don't know if it actually works """
    location = util.get_command_output(('grep', '-i', 'floppy', '/var/log/dmesg'))
    if len(location):
        location = re.search('(?m)^[Ff]loppy drive.*?: (\w+) ', location)
        if location:
            location = '/dev/%s' % location.groups()[0]
            if os.path.exists(location):
                return location
            else:
                location = '/dev/%s/%s' % (location[:2], location[-1])
                if os.path.exists(location):
                    return location
    return None

def get_internal_path_for_drive(drive_letter):
    for drive in [drive_letter[0].lower(), drive_letter[0].upper()]:
        path = "%s/dosdevices/%s:" % (common.ENV['WINEPREFIX'], drive)
        if os.path.exists(path) or os.path.islink(path):
            return path

def get_internal_path_for_drive_device(drive_letter):
    for drive in (drive_letter[0].lower(), drive_letter[0].upper()):
        path = "%s/dosdevices/%s::" % (common.ENV['WINEPREFIX'], drive)
        if os.path.exists(path) or os.path.islink(path):
            return path

def get_available_drive_letters():
    return [
        i for i in string.ascii_uppercase[3:]
        if i not in get(basic=True).keys()
    ]