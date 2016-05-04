#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

import util, registry, common

ACCELERATION_NAMES = {
    "default": "Full",
    "full": "Full",
    "standard": "Standard",
    "basic": "Basic",
    "emulation": "Emulation"
}
ACCELERATIONS = ACCELERATION_NAMES.keys()
RATES = [48000, 44100, 22050, 16000, 11025, 8000]
BITS = [8, 16]
DRIVER_NAMES = {
    'alsa':      'alsa',
    'oss':       'oss',
    'coreaudio': 'coraudio',
    'jack':      'jack',
    'nas':       'nas',
    'esd':       'esd',
    'audioio':   'audioio',
    'pulse':     'pulse'
}

def get_drivers():
    paths = [
        '{vineyard_path}/lib'.format(vineyard_path = common.ENV['VINEYARDPATH']),
        '/usr/lib',
        '/usr/lib32',
        '/usr/local/lib',
        '/usr/local/lib32'
    ]
    drivers_1 = util.get_command_output("grep -l -e 'winmm' %s" %
        ' '.join('%s/wine/wine*.drv.so' % i for i in paths), shell=True, dont_parse_command=True)
    drivers_2 = util.get_command_output("grep -l -e 'wave' %s" %
        ' '.join('%s/wine/wine*.drv.so' % i for i in paths), shell=True, dont_parse_command=True)
    return list(set(drivers_1.split('\n')) & set(drivers_2.split('\n')))

def get_driver_name(driverfile):
    return driverfile.split('/wine')[-1].split('.drv')[0]

DRIVERS = [ get_driver_name(driver) for driver in get_drivers() ]

def get_devices():
    output = {'out':{}, 'in':{}}
    devices = registry.get('HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\MMDevices\\Audio'
                                ,quiet=True)
    # Testing data:
    #devices = {'Capture': {'{F339B1DC-2C23-4841-A3D0-BD7E2B2C221F}': {'Properties': {u'{F19F064D-082C-4E27-BC73-6882A1BB8E4C},0': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},2': u'HDA ATI SB - ALC889A Digital', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},14': u'HDA ATI SB - ALC889A Digital', u'{E4870E26-3CC5-4CD2-BA46-CA0A9A70ED04},3': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71'}, u'DeviceState': u'dword:00000001'}, '{77B76B38-AB09-4BA3-AC05-DB3DB1423465}': {'Properties': {u'{F19F064D-082C-4E27-BC73-6882A1BB8E4C},0': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},2': u'HDA ATI SB - ALC889A Analog', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},14': u'HDA ATI SB - ALC889A Analog', u'{E4870E26-3CC5-4CD2-BA46-CA0A9A70ED04},3': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71'}, u'DeviceState': u'dword:00000001'}, '{FC420A03-7C59-49E4-A042-EDC9117F4014}': {'Properties': {u'{F19F064D-082C-4E27-BC73-6882A1BB8E4C},0': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},2': u'default', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},14': u'default', u'{E4870E26-3CC5-4CD2-BA46-CA0A9A70ED04},3': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71'}, u'DeviceState': u'dword:00000001'}}, 'Render': {'{50E55B21-BE90-4F49-897F-91251492D44B}': {'Properties': {u'{F19F064D-082C-4E27-BC73-6882A1BB8E4C},0': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},2': u'USB Sound Device - USB Audio', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},14': u'USB Sound Device - USB Audio', u'{E4870E26-3CC5-4CD2-BA46-CA0A9A70ED04},3': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71'}, u'DeviceState': u'dword:00000001'}, '{5137B298-5B1B-4948-B14A-2696B8C02110}': {'Properties': {u'{F19F064D-082C-4E27-BC73-6882A1BB8E4C},0': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},2': u'HDA ATI SB - ALC889A Digital', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},14': u'HDA ATI SB - ALC889A Digital', u'{E4870E26-3CC5-4CD2-BA46-CA0A9A70ED04},3': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71'}, u'DeviceState': u'dword:00000001'}, '{9F815751-4036-412E-AAEB-7D6AC3932230}': {'Properties': {u'{F19F064D-082C-4E27-BC73-6882A1BB8E4C},0': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},2': u'HDA ATI SB - ALC889A Analog', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},14': u'HDA ATI SB - ALC889A Analog', u'{E4870E26-3CC5-4CD2-BA46-CA0A9A70ED04},3': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71'}, u'DeviceState': u'dword:00000001'}, '{8792A66E-6D13-4F9E-A608-1E5D12494D49}': {'Properties': {u'{F19F064D-082C-4E27-BC73-6882A1BB8E4C},0': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},2': u'default', u'{A45C254E-DF1C-4EFD-8020-67D146A850E0},14': u'default', u'{E4870E26-3CC5-4CD2-BA46-CA0A9A70ED04},3': 'hex:fe,ff,02,00,80,bb,00,00,00,dc,05,00,08,00,20,00,16,00,20,00,03,00,00,00,03,00,00,00,00,00,10,00,80,00,00,aa,00,38,9b,71'}, u'DeviceState': u'dword:00000001'}}}
    for device_type,type_name in [('Render','out'), ('Capture','in')]:
        for device_id in devices[device_type].iterkeys():
            # This is a bit of a hack. I have no idea how this data is structured,
            # I just use the first value that is a string instead of a hex value
            device_properties = devices[device_type][device_id]['Properties']
            name = [ i for i in device_properties.itervalues() if type(i) == unicode ][0]

            output[type_name][name] = device_properties
            output[type_name][name]['id'] = device_id
    return output

# Examples:
#   By name:
#     audio.set_device('USB Sound Device - USB Audio')
#   By ID:
#     audio.set_device('{F339B1DC-2C23-4841-A3D0-BD7E2B2C221F}')
#   By audio.get_devices output (use first output)
#     audio.set_device(audio.get_devices()['out'].values()[0])
def set_device(id, direction='out'):
    if direction == 'out':
        output = 'DefaultOutput'
    elif direction == 'voice_out':
        output = 'DefaultVoiceOutput'
        direction = 'out'
    elif direction == 'in':
        output = 'DefaultInput'
    elif direction == 'voice_in':
        output = 'DefaultVoiceInput'
        direction = 'in'
    else:
        output = 'DefaultOutput'

    if type(id) == dict:
        # By get_devices output
        device_id = id['id']
    elif type(id) in (str, unicode):
        # By ID
        if id[0] == '{':
            device_id = id
        # By name
        else:
            devices = get_devices()
            device_id = devices[direction][id]['id']
    else:
        return false

    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Drivers\\winealsa.drv': {
                output: device_id}})


def get_acceleration(program=None):
    #try:
    #    return CACHE['audio-acceleration']
    #except KeyError:
    if program:
        level = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DirectSound' % \
            program, "HardwareAcceleration", quiet=True)
    else:
        level = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\DirectSound',
            "HardwareAcceleration", quiet=True)
    if level:
        #CACHE['audio-acceleration'] = level
        return level
    else:
        #CACHE['audio-acceleration'] = ACCELERATION_NAMES['default']
        return ACCELERATION_NAMES['default']

def set_acceleration(accel, program=None):
    """
        Sets the level of audio acceleration to use.
        accel can be one of ["full", "standard", "basic", "emulation"]
    """
    if program:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DirectSound' % \
            program: {"HardwareAcceleration": ACCELERATION_NAMES[accel]}})
    else:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DirectSound': {
            "HardwareAcceleration": ACCELERATION_NAMES[accel]}})
        #CACHE['audio-acceleration'] = ACCELERATION_NAMES[accel]

def get_sample_rate(program=None):
    if program:
        rate = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DirectSound' % program,
            "DefaultSampleRate", quiet=True)
    else:
        #try:
        #    return CACHE['audio-samplerate']
        #except KeyError:
        rate = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\DirectSound',
            "DefaultSampleRate", quiet=True)
    if rate:
        #if program == None:
        #    CACHE['audio-samplerate'] = rate
        return rate
    else:
        if program == None:
            CACHE['audio-samplerate'] = '44100'
        return '44100'

def set_sample_rate(rate, program=None):
    """
        Sets the DirectSound audio sample rate
    """
    if program:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DirectSound' % program: {
            "DefaultSampleRate": rate}})
    else:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DirectSound': {
            "DefaultSampleRate": rate}})
        #CACHE['audio-samplerate'] = str(rate)

def get_bit_depth(program=None):
    if program:
        bits = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DirectSound' % \
            program, "DefaultBitsPerSample", quiet=True)
    else:
        #try:
        #    return CACHE['audio-bitdepth']
        #except KeyError:
        bits = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\DirectSound',
            "DefaultBitsPerSample", quiet=True)
    if bits:
        #if program == None:
        #    CACHE['audio-bitdepth'] = bits
        return bits
    else:
        #if program == None:
        #    CACHE['audio-bitdepth'] = '16'
        return '16'

def set_bit_depth(bits, program=None):
    """
        Sets the DirectSound audio bit depth
    """
    if program:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DirectSound' % program: {
            "DefaultBitsPerSample": bits}})
    else:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DirectSound': {
            "DefaultBitsPerSample": bits}})
        #CACHE['audio-bitdepth'] = str(bits)

def get_driver_emulation(program=None):
    if program:
        state = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DirectSound' % program,
            "EmulDriver", quiet=True)
    else:
        #try:
        #    return CACHE['audio-emulate-driver']
        #except KeyError:
        state = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\DirectSound',
            "EmulDriver", quiet=True)
    if state and "y" in state.lower():
        #if program == None:
        #    CACHE['audio-emulate-driver'] = True
        return True
    else:
        #if program == None:
        #    CACHE['audio-emulate-driver'] = False
        return False

def set_driver_emulation(state, program=None):
    """
        Sets wether DirectSound should emulate a hardware driver
    """
    if state:
        state_str = "Y"
    else:
        state_str = "N"

    if program:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DirectSound' % program: {
            "EmulDriver": state_str}})
    else:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DirectSound': {
            "EmulDriver": state_str}})
        #CACHE['audio-emulate-driver'] = state

def get_enabled_drivers():
    #try:
    #    return CACHE['audio-enabled-drivers']
    #except KeyError:
    drivers = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\Drivers', "Audio", quiet=True)
    if drivers not in [ None, {} ]:
        drivers = drivers.split(',')
        #CACHE['audio-enabled-drivers'] = drivers
        return drivers
    else:
        #CACHE['audio-enabled-drivers'] = []
        return []

def set_enabled_drivers(drivers):
    """
        Sets the list of enabled audio drivers
        disabling all others
    """
    #CACHE['audio-enabled-drivers'] = drivers
    registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Drivers': {"Audio": ','.join(drivers)}})

def enable_driver(driver):
    """
        Adds an audio driver to the list of enabled audio drivers
        driver can be one of ["alsa", "oss", "coreaudio", "jack", "nas", "esd", "audioio"]
    """
    drivers = filter(len, get_enabled_drivers())
    print driver, DRIVER_NAMES
    if driver in DRIVER_NAMES and DRIVER_NAMES[driver] not in drivers:
        drivers.append(DRIVER_NAMES[driver])
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Drivers': {"Audio": ','.join(drivers)}})
    else:
        return False

def disable_driver(driver):
    """
        Removes an audio driver from the list of enabled audio drivers
        driver can be one of ["alsa", "oss", "coreaudio", "jack", "nas", "esd", "audioio"]
    """
    drivers = get_enabled_drivers()
    if driver in DRIVER_NAMES and DRIVER_NAMES[driver] in drivers:
        drivers.remove(DRIVER_NAMES[driver])
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\Drivers': {"Audio": ','.join(drivers)}})

def get_eax_support(program=None):
    if common.ENV.get('WINE_SUPPORTS_EAX') == 'true':
        if program:
            bits = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DirectSound' % \
                program, "EAXEnabled", quiet=True)
        else:
            enabled = registry.get('HKEY_CURRENT_USER\\Software\\Wine\\DirectSound',
                "EAXEnabled", quiet=True)
        if enabled:
            return common.value_as_bool(enabled) or False
        else:
            return False
    else:
        return None

def set_eax_support(value, program=None):
    """
        Enables or disables support for EAX on the CPU
    """
    value = common.value_as_bool(value)
    if value == None:
        raise ValueError("type of value should something convertable to a boolean")
    elif value == True:
        value = 'Y'
    else:
        value = None
    if program:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\AppDefaults\\%s\\DirectSound' % program: {
            "EAXEnabled": value}})
    else:
        registry.set({'HKEY_CURRENT_USER\\Software\\Wine\\DirectSound': {
            "EAXEnabled": value}})
