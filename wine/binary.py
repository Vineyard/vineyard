#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>
#
#
# Portions based on Jason Tackaberry's version reading code at:
# http://code.activestate.com/recipes/496973-get-version-from-win32-portable-executable-file/
# and Martin B's GetBinary replacement code at:
# http://stackoverflow.com/questions/1345632/determine-if-an-executable-or-library-is-32-or-64-bits-on-windows
#
# DWORD = 4 bytes (L)
# QWORD = 8 bytes (Q)

from __future__ import print_function

import struct, binascii

CPU_NAME = {
    0x0184: u"Alpha AXP",
    0x01c0: u"ARM",
    0x014C: u"Intel 80386",    # standard 32-bit
    0x014D: u"Intel 80486",
    0x014E: u"Intel Pentium",
    0x0200: u"Intel IA64",     # standard 64-bit according to the spec, actually only Intel Itanium and never really used
    0x8664: u"AMD 64",         # standard 64-bit, but not in the spec
    0x0268: u"Motorola 68000",
    0x0266: u"MIPS",
    0x0284: u"Alpha AXP 64 bits",
    0x0366: u"MIPS with FPU",
    0x0466: u"MIPS16 with FPU",
    0x01f0: u"PowerPC little endian",
    0x0162: u"R3000",
    0x0166: u"MIPS little endian (R4000)",
    0x0168: u"R10000",
    0x01a2: u"Hitachi SH3",
    0x01a6: u"Hitachi SH4",
    0x0160: u"R3000 (MIPS), big endian",
    0x0162: u"R3000 (MIPS), little endian",
    0x0166: u"R4000 (MIPS), little endian",
    0x0168: u"R10000 (MIPS), little endian",
    0x0184: u"DEC Alpha AXP",
    0x01F0: u"IBM Power PC, little endian",
}
WINDOWS_SUBSYSTEM = {
     0: 'unknown',
     1: 'Native',
     2: 'Windows GUI',
     3: 'Windows CUI',
     7: 'POSIX CUI',
     9: 'Windows CE GUI',
    10: 'EFI Application',
    11: 'EFI Boot Service Driver',
    12: 'EFI Runtime Driver',
    13: 'EFI ROM',
    14: 'XBOX',
}
OPTIONAL_HEADER_DIRECTORIES = {
     0: 'Export Table',
     1: 'Import Table',
     2: 'Resource Table',
     3: 'Exception Table',
     4: 'Certificate Table',
     5: 'Base Relocation Table',
     6: 'Debug',
     7: 'Architecture',
     8: 'Global Ptr',
     9: 'TLS Table',
    10: 'Load Config Table',
    11: 'Bound Import',
    12: 'IAT',
    13: 'Delay Import Descriptor',
    14: 'CLR Runtime Header',
    15: 'Reserved',
}
SECTION_FLAGS = {
    'reserved 1': (
        0x00000000),
 	'reserved 2': (
        0x00000001),
 	'reserved 3': (
        0x00000002),
 	'reserved 4': (
        0x00000004),
    'IMAGE_SCN_CNT_CODE': (
        0x00000020), #The section contains executable code.
    'IMAGE_SCN_CNT_INITIALIZED_DATA': (
        0x00000040), #The section contains initialized data.
    'IMAGE_SCN_CNT_UNINITIALIZED_': (
        0x00000080), #The section contains uninitialized data.
    'IMAGE_SCN_LNK_OTHER': (
        0x00000100), #Reserved for future use.
    'IMAGE_SCN_LNK_INFO': (
        0x00000200), #The section contains comments or other information. The .drectve section has this type. This is valid for object files only.
    'reserved 5': (
        0x00000400),
    'IMAGE_SCN_LNK_REMOVE': (
        0x00000800), #The section will not become part of the image. This is valid only for object files.
    'IMAGE_SCN_LNK_COMDAT': (
        0x00001000), #The section contains COMDAT data. For more information, see section 5.5.6, "COMDAT Sections (Object Only)." This is valid only for object files.
    'IMAGE_SCN_GPREL': (
        0x00008000), #The section contains data referenced through the global pointer (GP).
    'IMAGE_SCN_MEM_PURGEABLE': (
        0x00020000), #Reserved for future use.
    'IMAGE_SCN_MEM_16BIT': (
        0x00020000), #Reserved for future use.
    'IMAGE_SCN_MEM_LOCKED': (
        0x00040000), #Reserved for future use.
    'IMAGE_SCN_MEM_PRELOAD': (
        0x00080000), #Reserved for future use.
    'IMAGE_SCN_ALIGN_1BYTES': (
        0x00100000), #Align data on a 1-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_2BYTES': (
        0x00200000), #Align data on a 2-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_4BYTES': (
        0x00300000), #Align data on a 4-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_8BYTES': (
        0x00400000), #Align data on an 8-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_16BYTES': (
        0x00500000), #Align data on a 16-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_32BYTES': (
        0x00600000), #Align data on a 32-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_64BYTES': (
        0x00700000), #Align data on a 64-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_128BYTES': (
        0x00800000), #Align data on a 128-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_256BYTES': (
        0x00900000), #Align data on a 256-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_512BYTES': (
        0x00A00000), #Align data on a 512-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_1024BYTES': (
        0x00B00000), #Align data on a 1024-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_2048BYTES': (
        0x00C00000), #Align data on a 2048-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_4096BYTES': (
        0x00D00000), #Align data on a 4096-byte boundary. Valid only for object files.
    'IMAGE_SCN_ALIGN_8192BYTES': (
        0x00E00000), #Align data on an 8192-byte boundary. Valid only for object files.
    'IMAGE_SCN_LNK_NRELOC_OVFL': (
        0x01000000), #The section contains extended relocations.
    'IMAGE_SCN_MEM_DISCARDABLE': (
        0x02000000), #The section can be discarded as needed.
    'IMAGE_SCN_MEM_NOT_CACHED': (
        0x04000000), #The section cannot be cached.
    'IMAGE_SCN_MEM_NOT_PAGED': (
        0x08000000), #The section is not pageable.
    'IMAGE_SCN_MEM_SHARED': (
        0x10000000), #The section can be shared in memory.
    'IMAGE_SCN_MEM_EXECUTE': (
        0x20000000), #The section can be executed as code.
    'IMAGE_SCN_MEM_READ': (
        0x40000000), #The section can be read.
    'IMAGE_SCN_MEM_WRITE': (
        0x80000000) #The section can be written to.
}
SECTION_CHARACTERISTICS = {
#    '.bss': (
#        'IMAGE_SCN_CNT_UNINITIALIZED_DATA',
#        'IMAGE_SCN_MEM_READ',
#        'IMAGE_SCN_MEM_WRITE'),
#    '.cormeta': (
#        'IMAGE_SCN_LNK_INFO'),
    '.data': (
        'IMAGE_SCN_CNT_INITIALIZED_DATA',
        'IMAGE_SCN_MEM_READ',
        'IMAGE_SCN_MEM_WRITE'),
#    '.drective': (
#        'IMAGE_SCN_LNK_INFO'),
#    '.edata': (
#        'IMAGE_SCN_CNT_INITIALIZED_DATA',
#        'IMAGE_SCN_MEM_READ'),
#    '.idata': (
#        'IMAGE_SCN_CNT_INITIALIZED_DATA',
#        'IMAGE_SCN_MEM_READ',
#        'IMAGE_SCN_MEM_WRITE'),
#    '.idlsym': (
#        'IMAGE_SCN_LNK_INFO'),
#    '.pdata': (
#        'IMAGE_SCN_CNT_INITIALIZED_DATA',
#        'IMAGE_SCN_MEM_READ'),
#    '.rdata': (
#        'IMAGE_SCN_CNT_INITIALIZED_DATA',
#        'IMAGE_SCN_MEM_READ'),
#    '.reloc': (
#        'IMAGE_SCN_CNT_INITIALIZED_DATA',
#        'IMAGE_SCN_MEM_READ',
#        'IMAGE_SCN_MEM_DISCARDABLE'),
    '.rsrc': (
        'IMAGE_SCN_CNT_INITIALIZED_DATA',
        'IMAGE_SCN_MEM_READ'),
#    '.sxdata': (
#        'IMAGE_SCN_LNK_INFO'),
    '.text': (
        'IMAGE_SCN_CNT_CODE',
        'IMAGE_SCN_MEM_EXECUTE',
        'IIMAGE_SCN_MEM_READ'),
#    '.tls': (
#        'IMAGE_SCN_CNT_INITIALIZED_DATA',
#        'IMAGE_SCN_MEM_READ',
#        'IMAGE_SCN_MEM_WRITE'),
#    '.vsdata': (
#        'IMAGE_SCN_CNT_INITIALIZED_DATA',
#        'IMAGE_SCN_MEM_READ',
#        'IMAGE_SCN_MEM_WRITE'),
#    '.xdata': (
#        'IMAGE_SCN_CNT_INITIALIZED_DATA',
#        'IMAGE_SCN_MEM_READ')
}
#http://www.devsource.com/c/a/Architecture/Resources-From-PE-I/2/
RESOURCE_TYPES = {
    1: 'CURSOR',
    2: 'BITMAP',
    3: 'ICON',
    4: 'MENU',
    5: 'DIALOG',
    6: 'STRING',
    7: 'FONTDIR',
    8: 'FONT',
    9: 'ACCELERATOR',
    10: 'RCDATA',
    11: 'MESSAGETABLE',
    12: 'GROUP CURSOR',
    14: 'GROUP ICON',
    16: 'VERSION',
    17: 'DLGINCLUDE',
    19: 'PLUGPLAY',
    20: 'VXD',
    21: 'ANICURSOR',
    22: 'ANIICON',
    23: 'HTML',
    24: 'MANIFEST'
}
VERSION_INFO_OS = {
    0x00010000L: 'MS-DOS',
    0x00040000L: 'Windows NT',
    0x00000001L: '16-bit Windows',
    0x00000004L: '32-bit Windows',
    0x00020000L: '16-bit OS/2',
    0x00030000L: '32-bit OS/2',
    0x00000002L: '16-bit Presentation Manager',
    0x00000003L: '32-bit Presentation Manager',
    0x00000000L: 'Unknown'
}

LOG = False
def Log(*messages):
    if LOG:
        print(*messages)

class windows_executable(object):
    def __init__(self, file_path):
        self._file_path = file_path
        self._info_index = None
        file = open(self._file_path, 'rb')
        if file.read(2) != 'MZ':
            raise TypeError(
                "Given file is not a Windows executable: {0}".format(
                    file_path
            ))
        else:
            file.seek(60)
            self._header_offset = struct.unpack("<L", file.read(4))[0]
            file.seek(self._header_offset)
            if file.read(4) != "PE\0\0":
                raise ValueError(
                    "Invalid PE header signature in {0}".format(
                        file_path
            ))

            header = file.read(20)

            header_info = struct.unpack(
                '<HHLLLHH', header
            )
            self.header_coff = {
                'Machine': header_info[0],
                'NumberOfSections': header_info[1],
                'TimeDateStamp': header_info[2],
                'PointerToSymbolTable': header_info[3],
                'NumberOfSymbols': header_info[4],
                'SizeOfOptionalHeader': header_info[5],
                'Characteristics': header_info[6],
            }

            self.header_coff['Machine'] = CPU_NAME.get(
                self.header_coff['Machine'],
                self.header_coff['Machine']
            )

            if self.header_coff['SizeOfOptionalHeader']:
                self.type = 'executable'
                self._optional_header_offset = file.tell()
                self._read_optional_header(file)
                self._read_section_table(file)
            else:
                self.type = 'object'
        file.close()

    def _read_optional_header(self, file=None):
        we_opened_the_file = False
        if file is None or file.closed:
            file = open(self._file_path, 'rb')
            we_opened_the_file = True

        file.seek(self._optional_header_offset)
        magic = struct.unpack('<H', file.read(2))[0]
        if magic == 0x10b:
            # Optional header is in PE32 format
            self._optional_header_format = 'pe32'
        elif magic == 0x20B:
            # Optional header is in PE32+ format
            self._optional_header_format = 'pe32+'
        elif magic == 0x107:
            # File is a ROM image
            raise TypeError(
                "File is a ROM image, not an executable: {0}".format(
                    self._file_path
                )
            )

        # Standard IMAGE_NT_HEADERS32
        if '64' not in self.header_coff['Machine']:
            self.header_optional = {
                'MajorLinkerVersion': (
                    struct.unpack('<B', file.read(1))[0]),
                'MinorLinkerVersion': (
                    struct.unpack('<B', file.read(1))[0]),
                'SizeOfCode': (
                    struct.unpack('<L', file.read(4))[0]),
                'SizeOfInitializedData': (
                    struct.unpack('<L', file.read(4))[0]),
                'SizeOfUninitializedData': (
                    struct.unpack('<L', file.read(4))[0]),
                'AddressOfEntryPoint': (
                    struct.unpack('<L', file.read(4))[0]),
                'BaseOfCode': (
                    struct.unpack('<L', file.read(4))[0]),
                'BaseOfData': (
                    struct.unpack('<L', file.read(4))[0]),
            }
        # IMAGE_NT_HEADERS64
        else:
            self.header_optional = {
                'MajorLinkerVersion': (
                    struct.unpack('<B', file.read(1))[0]),
                'MinorLinkerVersion': (
                    struct.unpack('<B', file.read(1))[0]),
                'SizeOfCode': (
                    struct.unpack('<L', file.read(4))[0]),
                'SizeOfInitializedData': (
                    struct.unpack('<L', file.read(4))[0]),
                'SizeOfUninitializedData': (
                    struct.unpack('<L', file.read(4))[0]),
                'AddressOfEntryPoint': (
                    struct.unpack('<L', file.read(4))[0]),
                'BaseOfCode': (
                    struct.unpack('<L', file.read(4))[0]),
            }

        if self._optional_header_format == 'pe32':
            self.header_optional['ImageBase'] = (
                struct.unpack('<L', file.read(4))[0])
        elif self._optional_header_format == 'pe32+':
            self.header_optional['ImageBase'] = (
                struct.unpack('<Q', file.read(8))[0])
        self.header_optional['SectionAlignment'] = (
            struct.unpack('<L', file.read(4))[0])
        self.header_optional['FileAlignment'] = (
            struct.unpack('<L', file.read(4))[0])
        self.header_optional['MajorOSVersion'] = (
            struct.unpack('<H', file.read(2))[0])
        self.header_optional['MinorOSVersion'] = (
            struct.unpack('<H', file.read(2))[0])
        self.header_optional['MajorImageVersion'] = (
            struct.unpack('<H', file.read(2))[0])
        self.header_optional['MinorImageVersion'] = (
            struct.unpack('<H', file.read(2))[0])
        self.header_optional['MajorSubsystemVersion'] = (
            struct.unpack('<H', file.read(2))[0])
        self.header_optional['MinorSubsystemVersion'] = (
            struct.unpack('<H', file.read(2))[0])
        self.header_optional['Reserved'] = (
            struct.unpack('<L', file.read(4))[0])
        self.header_optional['SizeOfImage'] = (
            struct.unpack('<L', file.read(4))[0])
        self.header_optional['SizeOfHeaders'] = (
            struct.unpack('<L', file.read(4))[0])
        self.header_optional['Checksum'] = (
            struct.unpack('<L', file.read(4))[0])
        self.header_optional['Subsystem'] = (
            struct.unpack('<H', file.read(2))[0])
        self.header_optional['DLLCharacteristics'] = (
            struct.unpack('<H', file.read(2))[0])
        if self._optional_header_format == 'pe32':
            self.header_optional['SizeOfStackReserve'] = (
                struct.unpack('<L', file.read(4))[0])
            self.header_optional['SizeOfStackCommit'] = (
                struct.unpack('<L', file.read(4))[0])
            self.header_optional['SizeOfHeapReserve'] = (
                struct.unpack('<L', file.read(4))[0])
            self.header_optional['SizeOfHeapCommit'] = (
                struct.unpack('<L', file.read(4))[0])
        elif self._optional_header_format == 'pe32+':
            self.header_optional['SizeOfStackReserve'] = (
                struct.unpack('<Q', file.read(8))[0])
            self.header_optional['SizeOfStackCommit'] = (
                struct.unpack('<Q', file.read(8))[0])
            self.header_optional['SizeOfHeapReserve'] = (
                struct.unpack('<Q', file.read(8))[0])
            self.header_optional['SizeOfHeapCommit'] = (
                struct.unpack('<Q', file.read(8))[0])
        self.header_optional['LoaderFlags'] = (
            struct.unpack('<L', file.read(4))[0])
        self.header_optional['NumberOfRvaAndSizes'] = (
            struct.unpack('<L', file.read(4))[0])

        self.header_optional['Subsystem'] = WINDOWS_SUBSYSTEM.get(
            self.header_optional['Subsystem'],
            self.header_optional['Subsystem']
        )
        self.header_data_directories = {}
        for index in range(self.header_optional['NumberOfRvaAndSizes']):
            self.header_data_directories[
                OPTIONAL_HEADER_DIRECTORIES[index]
            ] = {
                'VirtualAddress': (
                    struct.unpack('<L', file.read(4))[0]),
                'Size': (
                    struct.unpack('<L', file.read(4))[0])
            }
        self._section_table_offset = file.tell()

        if we_opened_the_file:
            file.close()


    def _read_section_table(self, file=None):
        we_opened_the_file = False
        if file is None or file.closed:
            file = open(self._file_path, 'rb')
            we_opened_the_file = True

        file.seek(self._section_table_offset)
        self.sections = {}
        sections = {}
        for index in range(self.header_coff['NumberOfSections']):
            start = file.tell()
            name = file.read(8)
            name = struct.unpack('<8s', name)[0].replace('\x00','')
            name = name.decode('utf-8')

            Log("Reading section {0} at {1}".format(
                name,
                start
            ))
            section = {
                'VirtualSize': (
                    struct.unpack('<L', file.read(4))[0]),
                'VirtualAddress': (
                    struct.unpack('<L', file.read(4))[0]),
                'SizeOfRawData': (
                    struct.unpack('<L', file.read(4))[0]),
                'PointerToRawData': (
                    struct.unpack('<L', file.read(4))[0]),
                'PointerToRelocations': (
                    struct.unpack('<L', file.read(4))[0]),
                'PointerToLinenumbers': (
                    struct.unpack('<L', file.read(4))[0]),
                'NumberOfRelocations': (
                    struct.unpack('<H', file.read(2))[0]),
                'NumberOfLinenumbers': (
                    struct.unpack('<H', file.read(2))[0]),
                'Characteristics': (
                    struct.unpack('<L', file.read(4))[0]),
                'CharacteristicsValues': []
            }

            for key, value in SECTION_FLAGS.iteritems():
                if ( section['Characteristics'] & value ):
                    section['CharacteristicsValues'].append(key)

            """if not len(name.strip()) or name.strip() == '.':
                for key, value in SECTION_CHARACTERISTICS.iteritems():
                    print("Testing if these match:",(
                        tuple(section['CharacteristicsValues']),
                        value
                    ))
                    if (sorted([
                        i for i in value
                        if i in section['CharacteristicsValues']
                    ]) == sorted(value[:]) ):
                        name = key
                        break"""

            sections[name] = section

        if '.rsrc' in sections:
            self._resource_section = '.rsrc'
        else:
            self._resource_section = None

        for name in sorted(sections.keys()):
            section = sections[name]
            name = name
            if '$' in name:
                #name = name.split('$')[0]
                print(
                    "Oh! An addition to section {0}, will we handle this correctly?".format(
                        name
                    ))
            #if name not in self.sections:
            #    self.sections[name] = {}
            #
            #self.sections[name].update(section)
            self.sections[name] = section

            if self._resource_section is None:
                if (
                    'IMAGE_SCN_CNT_INITIALIZED_DATA'
                    in section['CharacteristicsValues']
                ) and (
                    'IMAGE_SCN_MEM_READ'
                    in section['CharacteristicsValues']
                ) and (
                    'IMAGE_SCN_MEM_EXECUTE'
                    not in section['CharacteristicsValues']
                ):
                    self._resource_section = name

        if we_opened_the_file:
            file.close()

    def read_resource_directory_table(self, section=None, rva=None, offset=None, file=None):
        we_opened_the_file = False
        if file is None or file.closed:
            file = open(self._file_path, 'rb')
            we_opened_the_file = True

        section_offset = 0
        if section is not None:
            section_offset = self.sections[section]['PointerToRawData']

        if offset is not None:
            offset = section_offset + offset
        else:
            offset = section_offset

        if rva is not None:
            offset = self.rva_to_offset(rva, section)

        Log("Read resource table for {0} at {1}".format(
            section,
            offset
        ))
        file.seek(offset, 0)

        table = {
            'Characteristics': (
                struct.unpack('<L', file.read(4))[0]),
            'TimeDateStamp': (
                struct.unpack('<L', file.read(4))[0]),
            'Major Version': (
                struct.unpack('<H', file.read(2))[0]),
            'Minor Version': (
                struct.unpack('<H', file.read(2))[0]),
            'Number of Name Entries': (
                struct.unpack('<H', file.read(2))[0]),
            'Number of ID Entries': (
                struct.unpack('<H', file.read(2))[0])
        }
        Log("Name Entries:", table['Number of Name Entries'], "ID Entries:", table['Number of ID Entries'])
        named_entries = []
        for i in range(table['Number of Name Entries']):
            Log("\tRead name entry {nr}, type 'name', section {section}".format(
                nr = i,
                section = section
            ))
            """entry = self._read_resource_directory_entry(
                file=file,
                type='name',
                section=section
            )
            named_entries.append(entry)"""
        table['Named Entries'] = named_entries
        id_entries = []
        """"for i in range(table['Number of ID Entries']):
            entry = self._read_resource_directory_entry(
                file=file,
                type='id',
                section=section
            )
            id_entries.append(entry)"""
        table['ID Entries'] = id_entries
        Log("Entries read, we are now at:", file.tell())
        Log("we started at {0}, that's a difference of {1}".format(
            offset,
            file.tell()-offset))

        if we_opened_the_file:
            file.close()

        return table

    def _read_resource_directory_entry(self, offset=None, rva=None, file=None, type=None, section=None):
        we_opened_the_file = False
        if file is None or file.closed:
            file = open(self._file_path, 'rb')
            we_opened_the_file = True

        if offset is not None:
            file.seek(offset, 0)
        elif rva is not None:
            file.seek(self.rva_to_offset(rva, section), 0)

        Log("Reading directory, we're currently at",file.tell())
        name = struct.unpack('<L', file.read(4))[0]
        data = struct.unpack('<L', file.read(4))[0]
        if type == 'name':
            table = {'Name RVA': name}
            table['Name'] = (
                self.read_resource_directory_string(name, section))
        else:
            table = {'Integer ID': name}
            if name in RESOURCE_TYPES:
                table['Type'] = RESOURCE_TYPES[name]

        # If high-bit is set, then this is the adress of another
        # resource directory table
        #
        # Here are some earlier attempts at getting this bit data, maybe it's
        # of use.
        #datas_first_high_bit = data & 0x40000000
        #datas_first_high_bit = bin(data)[2]
        #datas_first_high_bit = eval('0x{0}'.format(str(hex_data)[-2:]))
        #datas_lower_31_bits = data & 0x3fffffff
        #datas_lower_31_bits = data & 0x7fffffff
        #datas_lower_31_bits = eval('0x{0}'.format(str(hex_data)[:-2]))
        datas_full_hex = '0x'+'0'*(6-len(hex(data)[2:]))+hex(data)[2:]
        datas_first_high_bit = int(datas_full_hex[2:4], 16)
        datas_lower_31_bits = eval('0x00{0}'.format(datas_full_hex[4:]))
        Log("Data", data, datas_lower_31_bits)
        Log("    ", hex(data))
        Log("    ", "as an RVA that's",
            self.rva_to_offset(datas_lower_31_bits, section),
            '(%s)' % hex(self.rva_to_offset(datas_lower_31_bits, section)))
        Log("    ","read at", hex(file.tell()-4))
        if datas_first_high_bit:
            table['Subdirectory RVA'] = datas_lower_31_bits
            table['Subdirectory'] = (
                self.read_resource_directory_table(
                    section = section,
                    rva = datas_lower_31_bits
                )
            )
        else:
            table['Data Entry RVA'] = data
            table['Data Entry'] = (
                self.read_resource_data_entry(
                    datas_lower_31_bits,
                    section
                )
            )

        Log("Done reading directory, we're currently at",file.tell())
        if we_opened_the_file:
            file.close()

        return table

    def read_resource_directory_string(self, rva, section=None, file=None):
        we_opened_the_file = False
        if file is None or file.closed:
            file = open(self._file_path, 'rb')
            we_opened_the_file = True

        offset = self.rva_to_offset(rva, section)
        file.seek(offset, 0)

        try:
            length = struct.unpack('<H', file.read(2))[0]
            string = struct.unpack('<L', file.read(length))[0]
            string = string.decode('unicode').encode('utf-8')
            data = {
                'Length': length,
                'Unicode String': u'{0}'.format(string)

            }
            string.data = data
        except struct.error:
            return None

        if we_opened_the_file:
            file.close()

        return string

    def read_resource_data_entry(self, rva, section=None, file=None):
        we_opened_the_file = False
        if file is None or file.closed:
            file = open(self._file_path, 'rb')
            we_opened_the_file = True

        offset = self.rva_to_offset(rva, section)
        file.seek(offset, 0)
        Log("Reading entry, we are now at", offset)

        table = {
            'Data RVA': (
                struct.unpack('<L', file.read(4))[0]),
            'Size': (
                struct.unpack('<L', file.read(4))[0]),
            'Codepage': (
                struct.unpack('<L', file.read(4))[0]),
            'Reserved': (
                struct.unpack('<L', file.read(4))[0])
        }

        if we_opened_the_file:
            file.close()

        return table


    def rva_to_offset(self, rva, section_name):
        # The method below might be useful for calculating VAs
        """print("Convert RVA: {0}".format(rva))
        print("\tRVA + Virtual Section Offset: {0}".format(
            rva + self.sections[section_name]['VirtualAddress']
        ))
        print("\tConverted to FileSections, that's {0}".format(
            self.va_to_ra(self.sections[section_name]['VirtualAddress'] + rva)
        ))
        print("\tIt might also be {0}".format(
            rva + align_to_size(
                self.sections[section_name]['PointerToRawData'],
                self.header_optional['FileAlignment']
            )
        ))
        print("\tWe're however, from testing, settling on {0}".format(
            (rva - self.sections[section_name]['VirtualAddress']) +
            self.sections[section_name]['PointerToRawData']
        ))"""
        #return rva + align_to_size(
        #        self.sections[section_name]['PointerToRawData'],
        #        self.header_optional['FileAlignment']
        #)
        if rva >= self.sections[section_name]['VirtualAddress']:
            rva -= self.sections[section_name]['VirtualAddress']

        return (
            rva +
            align_to_size(
                self.sections[section_name]['PointerToRawData'],
                self.header_optional['FileAlignment']
            )
        )

    def va_to_ra(self, va):
        return roundup(
            va /
            float(self.header_optional['SectionAlignment'])
        ) * self.header_optional['FileAlignment']


    def get_sub_entries_from_resource_entry(self, entry):
        entries = []
        if 'Data Entry' in entry:
            entries.append(entry['Data Entry'])
        elif 'ID Entries' in entry:
            for e in entry['ID Entries']+entry['Named Entries']:
                sub_entries = self.get_sub_entries_from_resource_entry(e)
                for sub_entry in sub_entries:
                    entries.append(sub_entry)
        elif 'Subdirectory' in entry:
            sub_entries = self.get_sub_entries_from_resource_entry(entry['Subdirectory'])
            for sub_entry in sub_entries:
                entries.append(sub_entry)
        return entries

    def get_resource_entries(self, type_or_id):
        #resources = self.read_resource_directory_table('.rsrc')
        resources = self.read_resource_directory_table(self._resource_section)
        try:
            if type(type_or_id) is int:
                entry = [
                    entry for entry
                    in resources['ID Entries']+resources['Named Entries']
                    if 'Integer ID' in entry and entry['Integer ID'] == type_or_id
                ][0]
            else:
                entry = [
                    entry for entry
                    in resources['ID Entries']+resources['Named Entries']
                    if 'Type' in entry and entry['Type'] == type_or_id
                ][0]
            #return entry
            return self.get_sub_entries_from_resource_entry(entry)
        except IndexError:
            raise IndexError("Resource entry not found")

    def get_resource_data(self, rva_or_entry, size=None):
        if type(rva_or_entry) is dict:
            rva = rva_or_entry['Data RVA']
            size = rva_or_entry['Size']
        elif size is not None:
            rva = rva_or_entry
        else:
            raise AttributeError("Both RVA and size must be given if rva is not an entry dict")

        with open(self._file_path, 'rb') as file:
            #file.seek( self.rva_to_offset(rva, '.rsrc'), 0)
            file.seek( self.rva_to_offset(rva, self._resource_section), 0)
            data = file.read(size)
        return data

    def parse_fixedfileinfo(self, data):
        # http://msdn.microsoft.com/en-us/library/ms646997(v=VS.85).aspx
        data = struct.unpack('<'+'L'*13, data)
        info = dict(zip((
            'Signature',
            'StrucVersion',
            'FileVersionMS',
            'FileVersionLS',
            'ProductVersionMS',
            'ProductVersionLS',
            'FileFlagsMask',
            'FileFlags',
            'FileOS',
            'FileType',
            'FileSubType',
            'FileDateMS',
            'FileDateLS'
        ), data))

        for key in (
            'StrucVersion', 'FileVersionMS', 'FileVersionLS',
            'ProductVersionMS', 'ProductVersionLS'):
            info[key] = float('{0}.{1}'.format(
                int(hex(info[key])[2:-4]),
                int(hex(info[key])[-min(4, len(hex(info[key]))-2):])
            ))
        info['FileVersionString'] = '{0}.{1}'.format(
            info['FileVersionMS'], info['FileVersionLS']
        )
        info['ProductVersionString'] = '{0}.{1}'.format(
            info['ProductVersionMS'], info['ProductVersionLS']
        )
        fileOS_values = []
        for key, value in VERSION_INFO_OS.iteritems():
            if ( info['FileOS'] & key ):
                fileOS_values.append(value)
        info['FileOSValues'] = fileOS_values

        return info

    #def parse_stringstructure_data(self, data, length):


    def get_version_info(self, data=None):
        #http://msdn.microsoft.com/en-us/library/ms647001(v=VS.85).aspx
        if data is None:
            try:
                data = self.get_resource_data( self.get_resource_entries('VERSION')[0] )
            except:
                raise AttributeError("File does not have any version info")

        output = {}

        length, value_length, v_type = struct.unpack('<HHH', data[:6])

        # This next bit is just the string "VS_VERSION_INFO", no need to read it
        #key = struct.unpack('<30s', data[6:36])[0].decode('utf-16-le')

        # Compute padding by finding the index of the signature field of the
        # data section, which is always set to 0xFEEF04BD (\xbd\x04\xef\xfe)
        padding = data[36:].index('\xbd\x04\xef\xfe')
        value = data[36+padding:36+padding+value_length]
        output['File Info'] = self.parse_fixedfileinfo(value)
        # If the size indicates that there is more data, it will be a
        # StringFileInfo structure. Load it.
        if 36+padding+value_length < length+padding:
            offset = 36+padding+value_length
            sf_length, sf_value_length, sf_type = struct.unpack(
                '<HHH', data[offset:offset+6]
            )
            # Offset offset by the length of the packed string "StringFileInfo",
            # which is the next bit.
            offset += 6 + 27
            # Following this string is padding, so find where it ends.
            offset += get_size_of_padding(data[offset:])
            # Now read the StringTable structure that follows
            st_length, st_value_length, st_type = struct.unpack(
                '<HHH', data[offset:offset+6]
            )
            language_key = '0x'+struct.unpack(
                '<16s', data[offset+6:offset+6+16]
            )[0].decode('utf-16-le')
            offset += 6+16
            output['Language Key'] = language_key

            offset += get_size_of_padding(data[offset:], padding='\x00\x00')
            # Now read the Strings structure
            # http://msdn.microsoft.com/en-us/library/ms646987(v=VS.85).aspx
            #ss_length, ss_value_length, ss_type = struct.unpack(
            #    '<HHH', data[offset:offset+6]
            #)
            offset += get_size_of_padding(data[offset+6:], padding='\x00\x00')
            # The official Microsoft documentation on reading strings structures
            # does not match my test files, so a bit of parsing magic is
            # used instead.
            strings = dict([
                (
                    part.split('\x00')[0],
                    filter(len, part.split('\x00')[1:])[0]
                )
                for part
                in data[offset:].decode('utf-16-le').split('\x01')
                if len(part) > 3
            ])
            output['Strings'] = strings

        return output


    def get_version_fast(self, return_block=False):
        # This is a quick and dirty method to get the basic version info
        data = {}
        file = open(self._file_path, 'rb')
        try:
            file.seek(self.sections['.rsrc']['PointerToRawData'])
        except (KeyError, IOError):
            return data
        version_info = file.read(self.sections['.rsrc']['SizeOfRawData'])
        try:
            version_info = version_info.split(
                struct.pack("32s", u"VS_VERSION_INFO".encode("utf-16-le"))
            )[1]
        except IndexError:
            if return_block:
                return version_info
            else:
                return data

        if return_block:
            return version_info
        else:
            version_info = version_info.decode('utf-16-le', 'replace')
            for key in ('CompanyName', 'FileDescription',
                         'FileVersion', 'LegalCopyright',
                         'ProductName', 'ProductVersion'):
                try:
                    data[key] = ''.join(filter(len, version_info.split(
                        '\x01{0}\x00'.format(key)
                    )[1].split('\x00'))[0]).encode('utf-8')
                    # Parsing failed, remove this key again
                    if '\x01' in data[key]:
                        del data[key]
                except:
                    pass
            return data


    def parse_groupicon(self, data=None):
        if data is None:
            try:
                data = self.get_resource_data(
                    self.get_resource_entries('GROUP ICON')[0]
                )
            except struct.error:
                return None

        output = dict(zip((
            'reserved', 'resource id', 'number of images'
        ), struct.unpack('<HHH', data[:6])))
        output['images'] = {}

        for i in range(output['number of images']):
            image_data = struct.unpack('<BBBBHHLH', data[6+(i*14):6+(i*14)+14])
            image = dict(zip((
                'width', 'height', 'colors', 'reserved', 'planes', 'bitcount',
                'bytes in image'
            ), image_data[:-1]))
            output['images'][image_data[-1]] = image
        return output

    def get_icon(self, index=None, output=None):
        headers = self.parse_groupicon()
        if headers is None:
            return None
        """
        # FIXME: Does this get all headers, or just first one?
        header = self.get_resource_data( self.get_resource_entries('GROUP ICON')[0] )
        reserved, res_id, num_images = struct.unpack('<HHH', header[:6])
        (
            width, height, colours, reserved, planes, bitcount,
            bytes_in_image, image_id
        ) = struct.unpack('<BBBBHHLH', header[6:6+14])
        """
        # ICO format
        # http://www.iconolog.org/info/icoFormat.html
        header_ico  = struct.pack('<HHH',
            0, headers['resource id'], headers['number of images']
        )
        #header_ico += struct.pack(
        #    '<BBBBHHLL',
        #    width, height, colours, reserved, planes, bitcount,
        #    bytes_in_image, 22) # 22 = header(6) + header_ico(16)
        ico = header_ico
        data_offset = 6 # header(6)
        if index is None:
            for image_id, image in headers['images'].iteritems():
                data = self.get_resource_data(
                    self.get_resource_entries('ICON')[
                        headers['images'].keys().index(image_id)
                    ]
                )
                data_offset += 16*image_id
                ico += struct.pack(
                    '<BBBBHHLL',
                    image['width'], image['height'], image['colors'],
                    image['reserved'], image['planes'],
                    image['bitcount'], image['bytes in image'],
                    data_offset)
                data_offset += image['bytes in image']

        if output is None:
            return (
                ico
            )
        else:
            with open(output, 'wb') as _file:
                _file.write(ico)
            return True

    def is_64bit(self):
        return ('64' in self.header_coff['Machine'])



class windows_link(object):
    def __setitem__(self, key, value):
        self._dict[key] = value

    def __getitem__(self, key):
        return self._dict[key]

    def __contains__(self, key):
        return key in self._dict

    def __repr__(self):
        return '{self} {dict}'.format(
            self = super(windows_link, self).__repr__(),
            dict = self._dict.__repr__()
        )

    def __init__(self, file_path):
        self._dict = {}
        self._file_path = file_path
        self._data = File(self._file_path, 'rb', cached=True)
        if self._data.read('L') != 76:
            raise TypeError(
                "Given file is not a Windows shell link: {0}".format(
                    file_path
            ))

        data = {}
        data['guid'] = self._data.read('B'*16)
        if data['guid'] == (1, 20, 2, 0, 0, 0, 0, 0, 192, 0, 0, 0, 0, 0, 0, 70):
            data['type'] = 'shell link'
        data['flags: shortcut'] = self._data.read('L')
        data['shortcut flags'] = {}
        for bit, key in (
            (0, 'has id list'),
            (1, 'has link info'),
            (2, 'has name'),
            (3, 'has relative path'),
            (4, 'has work dir'),
            (5, 'has arguments'),
            (6, 'has icon'),
            (7, 'uses unicode')
        ):
            data['shortcut flags'][key] = bool(
                get_bit(data['flags: shortcut'], bit)
            )

        data['flags: target'] = self._data.read('L')
        data['target flags'] = {}
        for bit, key in (
            (0, 'is read only'),
            (1, 'is hidden'),
            (2, 'is system file'),
            (3, 'is volume label (impossible)'),
            (4, 'is directory'),
            (5, 'is modified since last backup (archive)'),
            (6, 'is encrypted (NTFS partition)'),
            (7, 'is normal'),
            (8, 'is temporary'),
            (9, 'is sparse file'),
            (10, 'has reparse point data'),
            (11, 'is compressed'),
            (12, 'is offline')
        ):
            data['target flags'][key] = bool(
                get_bit(data['flags: target'], bit)
            )

        data['creation time'] = self._data.read('Q')
        data['last access time'] = self._data.read('Q')
        data['modification time'] = self._data.read('Q')
        data['file length'] = self._data.read('L')
        data['icon number'] = self._data.read('L')
        data['show window'] = self._data.read('L')
        if data['show window'] == 1:
            data['show window'] = 'normal'
        elif data['show window'] == 2:
            data['show window'] = 'minimized'
        elif data['show window'] == 3:
            data['show window'] = 'maximized'
        data['hot key'] = self._data.read('H')
        # After this there are some reserved values that are always 0
        reserved = self._data.read(10)

        # Read the shell item id list, if it exists
        if data['shortcut flags']['has id list']:
            data['id list'] = self.__read_id_list()

        # File location info header
        if data['shortcut flags']['has link info']:
            data['file location info'] = self.__read_link_info()
            self['location'] = data['file location info']['location']

        use_unicode = data['shortcut flags']['uses unicode']
        if data['shortcut flags']['has name']:
            self['name'] = self.__read_string_data(unicode=use_unicode)
        if data['shortcut flags']['has relative path']:
            self['relative path'] = self.__read_string_data(unicode=use_unicode)
        if data['shortcut flags']['has work dir']:
            self['work dir'] = self.__read_string_data(unicode=use_unicode)
        if data['shortcut flags']['has arguments']:
            self['arguments'] = self.__read_string_data(unicode=use_unicode)
        if data['shortcut flags']['has icon']:
            self['icon'] = self.__read_string_data(unicode=use_unicode)

        self.data = data

        self['show window as'] = data['show window']

    def __read_id_list(self, offset = None):
        data = []
        size = self._data.read('h')
        # Get length of first item
        id_length = max(self._data.read('h')-2, 0)
        pos_start = self._data.offset-2

        while id_length != 0:
            # Get the data of first or previous item
            id_data = self._data.read(id_length)
            data.append( id_data )
            # Read the length of the next item, breaking if 0
            id_length = max(self._data.read('h')-2, 0)

        return data

    def __read_string_data(self, offset = None, unicode = True):
        if offset is None:
            offset = self._data.offset
        size = self._data.read('h', offset = offset)
        if unicode:
            size = size * 2
            string = self._data.read(size)
            string = string.decode('utf-16-le')
        else:
            string = self._data.read(size)
        # It's actually illegal to null-terminate these strings,
        # but I've seen it happen! 4 r34l y0!
        # Note that we keep any other null chars, so beware.
        if string[-1] == '\x00':
            string = '\x00'.join(string.split('\x00')[:-1])
        return string

    def __read_link_info(self):
        offset = self._data.offset
        data = {}
        length = self._data.read('L')
        offset_info_header = self._data.read('L')
        _flags = self._data.read('L')
        flags = {}
        if offset_info_header >= 0x00000024:
            flags['has optional fields'] = True
        else:
            flags['has optional fields'] = False
        for bit, key in (
            (0, 'has volume id and base path'),
            (1, 'has network relative link')
        ):
            flags[key] = bool(
                get_bit(_flags, bit)
            )
        if (
            flags['has optional fields'] and
            flags['has volume id and base path']
        ):
            flags['has local base unicode'] = True
        else:
            flags['has local base unicode'] = False

        # Got the flags/info, load what they say is there
        offset_local_volume_table = self._data.read('L')
        offset_local_base_path = self._data.read('L')      # ascii
        offset_network_volume_table = self._data.read('L')
        offset_base_name = self._data.read('L')            # ascii
        if flags['has local base unicode']:
            offset_local_base_path = self._data.read('L')  # unicode
        if flags['has optional fields']:
            offset_base_name = self._data.read('L')        # unicode

        location = ''
        if flags['has volume id and base path']:
            data['volume id'] = self.__read_volume_table(
                offset = offset_local_volume_table + offset
            )
            data['local base path'] = self._data.read(
                length-(offset_local_base_path-offset),
                offset = offset_local_base_path+offset
            ).split('\x00')[0]
            location += data['local base path']
        else:
            # FIXME: We should (if we want to) load the network_volume_table
            # I can't test it though, as I've yet to come across a file that
            # contains this section
            location = 'network'
        data['base name'] = self._data.read(
            length-(offset_base_name-offset),
            offset = offset_base_name+offset
        ).split('\x00')[0]
        # The previous read went all the way to the end, so go back to
        # where the value actually ende (plus null byte)
        self._data.offset = offset_base_name + offset + len(data['base name'])+1
        location += data['base name']

        data['location'] = location
        # How do I get the size of this field (and the following)?
        #data['file location info']['local base path'] =
        return data

    def __read_volume_table(self, offset = None):
        data = {}
        if offset is None:
            offset = self._data.offset
        size = self._data.read('L', offset = offset)
        drivetype = self._data.read('L')
        if drivetype == 0x00000000:
            data['drive type'] = 'unknown'
        elif drivetype == 0x00000001:
            data['drive type'] = 'not mounted'
        elif drivetype == 0x00000002:
            data['drive type'] = 'removable'
        elif drivetype == 0x00000003:
            data['drive type'] = 'fixed'
        elif drivetype == 0x00000004:
            data['drive type'] = 'network'
        elif drivetype == 0x00000005:
            data['drive type'] = 'cdrom'
        elif drivetype == 0x00000006:
            data['drive type'] = 'ram'
        data['serial number'] = self._data.read('L')
        volume_label_offset = self._data.read('L') # ascii label
        if volume_label_offset == 0x00000014:
            # Does this field exist if 'volume label offset' != 0x00000014?
            volume_label_offset = self._data.read('L') # unicode label

        data['label'] = self._data.read(
            size-volume_label_offset,
            offset = offset+volume_label_offset
        )
        data['label'] = data['label'].split('\x00')[0]
        return data




def read(data, length, offset = None):
    if offset is None and type(data) is str:
        offset = 0

    use_struct = False
    if type(length) is str:
        use_struct = length[:]
        new_length = 0
        endianness = '<'
        if use_struct[0] == '<' or use_struct[0] == '>':
            endianness = use_struct[0]
            use_struct = use_struct[1:]

        if use_struct.lower() == 'byte':
            use_struct = 'B'
        elif use_struct.lower() == 'word':
            use_struct = 'H'
        for char in use_struct:
            if char == 'c':
                new_length += 1
            elif char == 'b':
                new_length += 1
            elif char == 'B':
                new_length += 1
            elif char == '?':
                new_length += 1
            elif char == 'h':
                new_length += 2
            elif char == 'H':
                new_length += 2
            elif char == 'i':
                new_length += 4
            elif char == 'I':
                new_length += 4
            elif char == 'l':
                new_length += 4
            elif char == 'L':
                new_length += 4
            elif char == 'q':
                new_length += 8
            elif char == 'Q':
                new_length += 8
            elif char == 'f':
                new_length += 4
            elif char == 'd':
                new_length += 8
        length = new_length
        if use_struct[0] != '<' and use_struct[0] != '>':
            use_struct = '<'+use_struct

    if type(data) is str:
        data = data[offset:offset+length]
    else:
        if offset:
            data.seek(offset)
        data = data.read(length)

    offset = offset+length

    if use_struct is not False:
        data = struct.unpack(use_struct, data)
        if len(data) == 1:
            data = data[0]
    """print("Read {start}-{end} of type {type}: {data}".format(
        start = offset,
        end = self.offset,
        type = use_struct,
        data = data
    ))"""
    return (data, offset)


class File(object):
    def __init__(self, path, mode='rb', cached=False):
        self._file = open(path, mode)
        if cached:
            self._data = self._file.read()
            self._file.close()
        self.cached = cached
        self.offset = 0

    def close(self):
        if not self._file.closed:
            self._file.close()

    def read(self, length, offset = None):
        if offset is None:
            offset = self.offset

        if self.cached:
            data, self.offset = read(self._data, length, offset)
        else:
            data, self.offset = read(self._file, length, offset)
        return data

def get_bit(value, bit):
    return (value >> bit) & 1

def roundup(number):
    return int(number)+int(divmod(number, 1)[1] != 0)

def align_to_size(number, alignment_size):
    number_fits_n_times = roundup(number / float(alignment_size))
    return alignment_size * number_fits_n_times

def get_size_of_padding(string, padding='\x00'):
    data = string.split(padding)
    padding_size = len(padding)
    padding_length = 0
    for i in range(len(data)):
        if data[i] == '':
            padding_length += padding_size
        else:
            break
    return padding_length