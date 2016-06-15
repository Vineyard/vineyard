#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2007-2010 Christian Dannie Storgaard
#
# AUTHOR:
# Christian Dannie Storgaard <cybolic@gmail.com>

from __future__ import print_function

import os, sys, random, string, re, fnmatch, subprocess, logging
import urllib2, time
import tarfile, zipfile
import common, drives, prefixes, registry, binary

logger = logging.getLogger("python-wine.util")
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error
critical = logger.critical

SUPPORTED_ARCHIVE_MIMETYPES = (
    'application/x-gzip', 'application/x-bzip2', 'application/zip'
)

def get_print_in_cols(data, spacing=8, right_align_last=False):
    if not len(data):
        return ""

    columns = {}
    # Re-arrange the data into columns so we can get the column widths
    for row in data:
        if len(row):
            for col_nr in range(len(row)):
                if col_nr not in columns:
                    columns[col_nr] = []
                columns[col_nr].append(row[col_nr])
        else:
            for col_nr in columns:
                columns[col_nr].append('')
    column_lengths = [ len(sorted(columns[key], cmp=lambda x,y: len(y)-len(x))[0]) for key in sorted(columns.keys()) ]

    # Format our new data into a string
    output = ''
    for row_nr in range(len(data)):
        line = ''
        if len(data[row_nr]):
            for column_nr in range(len(columns)):
                if column_nr == len(columns)-1:
                    if right_align_last:
                        line = "{line}{text:>{column_width}}".format(
                            line = line,
                            text = columns[column_nr][row_nr],
                            column_width = column_lengths[column_nr]
                        )
                    else:
                        line += columns[column_nr][row_nr]
                else:
                    # Pre Python 2.6
                    #column = columns[column_nr][row_nr]
                    #line += eval('"%-'+str(column_lengths[column_nr]+tab_width)+'s" % column')
                    # Python 2.6 and later
                    line = "{line}{text:<{column_width}}".format(
                        line = line,
                        text = columns[column_nr][row_nr],
                        column_width = column_lengths[column_nr]+spacing
                    )
            output = '%s\n%s' % (output, line)
        else:
            output = '%s\n' % output
    return output[1:]

def print_in_cols(data, **kwargs):
    print(get_print_in_cols(data, **kwargs))

def hextoutf8(string):
    """ Remove any leading 'hex:' or 'hex(2):' or similar """
    if 'hex' in string[:8] and ':' in string[:8]:
        string = string.split(':')[1]
    """ Remove any formatting of the string """
    # Using string.replace is actually 3 times faster than regex, but it's not as safe
    #string = string.strip().replace('\\','').replace('\n','').replace(' ','').replace(',','')
    string = re.sub(r'(?i)[^a-z0-9]','', string)

    """ Convert from unicode hex to utf-8 """
    #return string.strip().decode('hex').decode('raw_unicode_escape', 'replace').encode('utf-8')
    #return string.strip().decode('hex').encode('utf-8').decode('string_escape')
    return string.strip().decode('hex')

def utf8tohex(string):
    # Convert from utf-8 to unicode hex
    string = string.decode('utf-8').encode('raw_unicode_escape').encode('hex')+'00'
    # Format unicode hex into Wine Registry format (comma separated chars)
    return ','.join( [string[i]+string[i+1] for i in range(0, len(string), 2)] )

def stringtoutf8(string):
    #return string.encode('string_escape').encode('utf-8').replace('\\\\', '\\').replace('\\\\', '\\').replace('\x00','')
    return string.replace('\\\\', '\\').replace('\\\\', '\\').replace('\x00','')

def string_safe_chars(string, safe_chars=None, replacement_char='_', remove_repeats=False, extra_safe_chars=''):
    if (
        safe_chars is None or
        type(safe_chars) not in (list, tuple, str, unicode)
    ):
        safe_chars = (
            sys.modules['string'].ascii_letters+
            sys.modules['string'].digits
        )+extra_safe_chars

    new_string = []
    for i in string:
        if i in safe_chars:
            new_string.append(i)
        elif (
            not remove_repeats
        ) or (
            remove_repeats and new_string[-1] != replacement_char
        ):
            new_string.append(replacement_char)
    return ''.join(new_string)

def string_safe_win(string, replace_char=None):
    """Return a version of the string safe for Windows filesystems."""
    new_string = []
    for i in string:
        if i not in '|\\?*<":>+[]/':
            new_string.append(i)
        elif type(replace_char) in (str, unicode):
            new_string.append(replace_char)
    return ''.join(new_string)

def string_safe_shell(string):
    if string.startswith("'") and string.endswith("'"):
        return string
    else:
        return string_escape_char(
            string,
            str(
                '&();|\n'+  # Control operators
                '<>'+       # Redirection operators
                '!*?[]'+    # Shell patterns
                '$'         # Variables
            )
        )

def string_escape_char(string, char):
    """Escape the given character, ignoring any that are already escaped.
    Char can be a list, tuple or string of characters."""
    for index in range(len(char)):
        _char = char[index]
        if '\\' in char and _char != '\\':
            reg_expr = r'(?<!\\\\)[{0}]'
        else:
            reg_expr = r'(?<!\\)[{0}]'
        reg_expr = reg_expr.format(
            _char.replace('^', '\\^'
            ).replace(']', '\\]'
            ).replace('-', '\\-'
            ).replace('\\', '\\\\')
        )
        debug("wine.util.string_escape_char: Using expression: {0}".format(reg_expr))
        string = re.sub(
            reg_expr,
            '\\{0}'.format(_char),
            string
        )
    return string

def string_remove_escapes(string):
    for char in (' ', '"', "'", '(', ')', '`', '$', '!'):
        string = string.replace('\\{0}'.format(char), char)
    return string

def string_remove_quotes(string):
    if type(string) not in (str, unicode):
        return string

    for char in ('"', "'"):
        if string.startswith(char) and string.endswith(char):
            return string[1:-1]

def get_win_env(key=None):
    # Get the system environment
    env_system = registry.get((
        'HKEY_LOCAL_MACHINE\\System\\' +
        'CurrentControlSet\\Control\\Session Manager\\Environment'))
    # Get the user environment
    env_user = registry.get((
        'HKEY_CURRENT_USER\\' +
        'Environment'))
    # Start with the system keys
    env = env_system
    # Let the user-set ones override them
    env.update(env_user)

    if key is None:
        return env
    else:
        if key in env:
            return env[key]
        else:
            env_lowercase = dict(( (key.lower(), value) for key, value in env.iteritems() ))
            if key in env_lowercase:
                return env_lowercase[key]
            elif key.lower() in env_lowercase:
                return env_lowercase[key.lower()]
    return None

def get_win_env_path(key, insensitive=False, userenv=False):
    """Get a path key from the Wine environment, quick and dirty"""
    if userenv:
        filename = 'user.reg'
        start = '[Environment]'
    else:
        filename = 'system.reg'
        start = '[System\\\\CurrentControlSet\\\\Control\\\\Session Manager\\\\Environment]'
    if insensitive:
        start = start.lower()

    # Get the environment part of the reg file
    env = file_get_part(
        '{0}/{1}'.format(
            common.ENV['WINEPREFIX'],
            filename
        ),
        start,
        '\n\n',
        insensitive = insensitive
    )
    # Search for the key
    result = re.search(
        '"{key}"="(.*?)\n'.format(key = key),
        env
    )
    if result:
        # Got it
        result = result.groups()[0][:-1]
    else:
        # Didn't get it, try insensitively
        result = re.search(
            '(?i)"{key}"="(.*?)\n'.format(key = key),
            env
        )
        if result:
            # Got it
            result = result.groups()[0][:-1]
        else:
            # Didn't get it, try getting it from Wine in another way
            # FIXME: This is slow, can we speed it up somehow?
            result = common.run(
                [common.ENV['WINE'], 'cmd.exe', '/c', 'echo', '%{0}%'.format(key)],
                env = common.ENV_NO_DISPLAY(common.ENV_NO_GECKO())
            )[0].strip()
            if not len(result):
                return None
    # Remove double backslashes, except from the drive part
    result = result.replace('\\\\', '\\').replace('\\\\', '\\')
    result = result.replace(':\\', ':\\\\')
    return result

def dir_win(path, drives_info=None):
    unix_path = wintounix(path, drives_info=drives_info)
    if os.path.exists(unix_path):
        if os.path.isdir(unix_path):
            return os.listdir(unix_path)
        else:
            return path
    else:
        return None

def convert_wine_path_variables(path):
    if path.count('%') >= 2:
        # The path uses registry keys, let's load them
        env = get_win_env()
        # And then convert all the keys to lowercase
        env = dict(( (key.lower(), value) for key, value in env.iteritems() ))

        # Replace all the registry keys with their value
        keys_to_replace = set(re.findall('%([\w\d_\-]+)%', path))
        for key in keys_to_replace:
            if key.lower() in env:
                value = env[key.lower()]
            else:
                value = get_win_env_path(key, insensitive=True)
                if value is None:
                    value = get_win_env_path(key, insensitive=True, userenv=True)
                if value is None:
                    continue
            path.replace(
                '%{0}%'.format(key),
                value.replace('\\\\', '\\').replace('\\\\', '\\')
            )
    return path

def wintounix(path, drives_info=None):
    # Test if we can actually convert this path, skip it if we can't
    if not (
        path[1:3] == ':\\' or path[0] == '%'
    ) and not (
        path.startswith('..\\') or path.startswith('.\\')
    ):
        return path

    if drives_info == None:
        drives_info = drives.get(use_registry=False)
    else:
        drives_info = drives_info

    path = convert_wine_path_variables(path)

    if path[0].upper() in drives_info.keys():
        if drives_info[path[0].upper()]['mapping'].endswith('/'):
            mapping = drives_info[path[0].upper()]['mapping'][:-1]
        else:
            mapping = drives_info[path[0].upper()]['mapping']
        path = '%s/%s' % ( mapping, "/".join(path[3:].split("\\")).replace('\0','') )
    elif path[0] != '%':
        path = "%s/drive_c/%s" % (common.ENV['WINEPREFIX'], "/".join(path[3:].split("\\")).replace('\0',''))

    if not os.path.exists(path) and path[0] != '%':
        """Path does not exist, trying magic..."""
        newpath = ''
        for branch in filter(len, path.split('/')):
            temppath = '%s/%s' % (newpath, branch)
            """\tTesting %s..." % temppath"""
            if not os.path.exists(temppath):
                """\tDidn't work, iterating dir..."""
                pathlist = os.listdir(newpath)
                for filename in pathlist:
                    if '~' in branch and filename.lower().startswith(branch.lower().split('~')[0]) \
                    or filename.lower() == branch.lower():
                        temppath = '%s/%s' % (newpath, filename)
                        """\tMatch found in %s." % temppath"""
                        break
            if os.path.exists(temppath):
                newpath = temppath
                """\tGot a match on \"%s\"" % newpath"""
            else:
                """\tCouldn't match, returning \"%s\"" % path"""
                return '{0}/{1}'.format(temppath, path[len(temppath):])
        """Final result:", newpath"""
        path = newpath
    return os.path.normpath(path)

def unixtowin(path):
    """ See http://msdn.microsoft.com/en-us/library/aa365247(VS.85).aspx for info on Windows filenames """
    if path[1:3] == ':\\':
        return path

    drives_info = drives.get(use_registry=False)
    # Strip the drives info to be in the form {'/mapping/of/drive', 'C'} so we can sort it
    drives_info = dict([ (v['mapping'], k) for k,v in drives_info.iteritems() ])
    # Go through the mappings, sorted by length of mapping, longest first
    for mapping in sorted(drives_info.keys(), key=len, reverse=True):
        drive_letter = drives_info[mapping]
        # Make sure the mapping uses the same format as the path
        # otherwise translation gets tricky.
        # Only do it if this mapping is in the same prefix though.
        if (
            mapping.split('/')[-1].startswith('drive_') and
            '/.wine/drive' not in path and
            path.split('.wine')[0] == mapping.split('.wine')[0]
        ):
            drive = mapping[-1].lower()
            for _drive_letter in (mapping[-1].lower(), mapping[-1].upper()):
                mapping_remapped = '{prefix}/dosdevices/{drive}:'.format(
                    prefix = mapping.split('/drive_')[0],
                    drive = _drive_letter
                )
                if os.path.exists(mapping_remapped):
                    mapping = mapping_remapped
                    break

        if path.startswith(mapping):
            path = mapping.join(
                path.split(mapping)[1:]
            )

            path = path.replace('\\','~')
            for i in ['<', '>', ':', '"', '|', '?', '*']:
                path = path.replace(i, '~')

            return '{drive}:\\{path}'.format(
                drive = drive_letter,
                path = path
            ).replace('/', '\\').replace('\\\\', '\\')

def enhance_windows_path(path):
    """Replace special Vineyard variables in a path with their meaning.
    So far there is only one: CDROM:\\ for automatic finding and/or adding of an optical disc."""
    if path.startswith('CDROM:\\'):
        # Find the drives that are listed as a CDROM type
        _drives = drives.get()
        cdroms = dict([
            (key, value) for key, value in _drives.iteritems()
            if (
                'type' in value and value['type'] == 'cdrom' or
                'type' not in value
            )
        ])
        cdrom_drive = 'D' # fallback default
        drive_is_found = False

        if len(cdroms):
            # Use the first CDROM drive that has the requested file
            for drive, info in cdroms.iteritems():
                try:
                    debug("CDROM: Trying dir: {0}".format(
                        info['mapping']
                    ))
                    if os.path.exists(
                        wintounix(
                            '{0}:{1}'.format(
                                drive,
                                string_remove_from_start(
                                    path,
                                    'CDROM:'
                                )
                            ),
                        drives_info = cdroms)
                    ):
                        cdrom_drive = drive
                        drive_is_found = True
                        debug("CDROM: Using Wine mapping ({0})".format(
                            cdrom_drive
                        ))
                        break
                except OSError:
                    continue

        if not drive_is_found:
            # Check to see if there is a mounted CD or DVD
            # and use it's path
            mount_point = mount_name = None
            mounted_cds = get_mounted_cds()
            for mount in mounted_cds:
                test_path = wintounix(
                    'D:{0}'.format(
                        string_remove_from_start(
                            path,
                            'CDROM:'
                        )
                ))

                debug("Trying if mounted disc matches:", test_path,
                    {'D': {
                        'mapping': mount['dir']
                    }}
                )
                if os.path.exists(test_path,
                    drives_info = {'D': {
                        'mapping': mount['dir']
                    }}
                ):
                    mount_point = mount['dir']
                    mount_name = filter(len, mount_point.split('/'))[-1]

            if mount_point is None:
                # No CD or DVD found, use the Windows default
                # and hope for the best
                debug("CDROM: Using Windows default ({0})".format(
                    cdrom_drive
                ))
                # the default is defined earlier
            else:
                # We found a mounted CD or DVD
                # Add it as a drive in the configuration
                available_drive_letters = [
                    i for i in string.ascii_uppercase[3:]
                    if i not in _drives.keys()
                ]
                cdrom_drive = available_drive_letters[0]
                debug("Adding drive:", (
                    cdrom_drive,
                    mount_point,
                    mount_name,
                    'cdrom'
                ))
                drives.add(
                    cdrom_drive,
                    mount_point,
                    label = mount_name,
                    drive_type = 'cdrom'
                )
                debug("CDROM: Using mounted drive ({0})".format(
                    mount_point
                ))

        path = '{0}:{1}'.format(
            cdrom_drive,
            string_remove_from_start(path, 'CDROM:')
        )
    return path

def path_exists(path, ignore_broken_symlinks=True):
    """Test whether a path exists, either as a UNIX path or a Windows path"""
    def __path_exists(path):
        return (
            (
                ignore_broken_symlinks and os.path.lexists(path)
            ) or (
                not ignore_broken_symlinks and os.path.exists(path)
            )
        )

    if __path_exists(path):
        # Is this is a UNIX path?
        return True
    else:
        # No? Okay, how about a Windows path?
        if __path_exists(wintounix(path)):
            # The converted path exists? Great, return True
            return True
        else:
            return False

def find_files_containing_string(path, string, endswith=None, ignore_case=False, return_file_content=False):
    if endswith is not None:
        endswith = endswith.lower()
    if ignore_case:
        string = string.lower()

    for root, dirs, files in os.walk(path):
        for filename in files:
            if endswith is not None and not filename.lower().endswith(endswith):
                continue
            filename = '{0}/{1}'.format(root, filename)
            with open(filename, 'r') as file_obj:
                content = file_obj.read()
                if ignore_case:
                    if string in content.lower():
                        if return_file_content:
                            yield (filename, content)
                        else:
                            yield filename
                else:
                    if string in content:
                        if return_file_content:
                            yield (filename, content)
                        else:
                            yield filename

def string_remove_from_start(string, remove):
    return remove.join(string.split(remove)[1:])

def string_remove_duplicate(string, char):
    return char.join(filter(len, string.split(char)))

def string_random(length=5):
    return ''.join([
        random.choice(string.letters+string.digits)
        for i
        in range(length)
    ])
tempstring = string_random

def tempname(prefix='', ext=''):
    return "%s/%s%s%s" % (common.ENV['VINEYARDTMP'], prefix, string_random(), ext)

def bytes_to_other(bytes, size_unit='bytes', return_float=False):
    # Nice overview on defaults here:
    # https://wiki.ubuntu.com/UnitsPolicy
    if size_unit.lower() in ('bytes', 'b'):
        size_unit = 1
    elif size_unit.lower() in ('kilobytes','kb'):
        size_unit = 1000
    elif size_unit.lower() in ('kibibytes','kib'):
        size_unit = 1024
    elif size_unit.lower() in ('megabytes','mb'):
        size_unit = 1000000
    elif size_unit.lower() in ('megabytes2','mb2'):
        size_unit = 1024000
    elif size_unit.lower() in ('mebibytes','mib'):
        size_unit = 1048576
    elif size_unit.lower() in ('gigabytes','gb'):
        size_unit = 1000000000
    elif size_unit.lower() in ('gibibytes','gib'):
        size_unit = 1073741824
    elif size_unit.lower() in ('terabytes','tb'):
        size_unit = 1000000000000
    elif size_unit.lower() in ('tebibytes','tib'):
        size_unit = 1099511627776
    else:
        raise(ValueError, "size_unit is not recognised.")

    if return_float:
        return bytes / float(size_unit)
    else:
        return int(round(bytes / float(size_unit) ))

def get_number_of_files_in_dir(path):
    return sum([ len(files) for (path,dirs,files) in os.walk(path) ])

def get_file_size(file_path, size_unit='bytes', return_float=False):
    try:
        size = int(os.stat(file_path).st_size)
    except OSError:
        size = 0
    return bytes_to_other(size, size_unit, return_float)

def file_search_regex(file_path, string):
    with open(file_path, 'r') as _file:
        result = re.search(string, _file.read())
        return result

def file_get_part(file_path, start, end, insensitive=False, including=False):
    """Get the part of the file between start and end.
If including is true, the start and end strings are returned intact"""
    with open(file_path, 'r') as _file:
        if insensitive:
            data = _file.read().lower()
        else:
            data = _file.read()
    data = data.split(start)[1]
    data = data.split(end)[0]
    if including:
        data = '{0}{1}{2}'.format(start, data, end)
    return data

def file_get_index_of_string(file_path, string, reverse=False, bufsize=4096):
    if reverse:
        with open(file_path, 'r', bufsize) as _file:
            _file.seek(-1, 2)
            position = _file.tell()
            _buffer = ''
            while position:
                read_size = min(bufsize, position)
                _file.seek(-read_size, 1)
                _buffer = _file.read(read_size)
                if string in _buffer:
                    return int(position - (bufsize - _buffer.index(string)))
                _file.seek(-read_size, 1)
                position = _file.tell()
    else:
        with open(file_path, 'r', bufsize) as _file:
            # Get size of file
            _file.seek(-1, 2)
            file_size = _file.tell()
            # Return to beginning of file and get position
            _file.seek(0, 0)
            position = _file.tell()
            _buffer = ''
            while position < file_size:
                read_size = min(bufsize, file_size-position)
                _buffer = _file.read(read_size)
                if string in _buffer:
                    return int(position + _buffer.index(string))
                position = _file.tell()

def get_file_type(file_path):
    """ Only recognises archive types for now """
    output = get_command_output(['file', '-b', '--mime', file_path])

    if len(output.strip()):
        #output = ':'.join(output.split(':')[1:]).strip()
        if output.startswith('application/x-gzip'):
            if common.any_in_string(('.tar.', '.tgz'), file_path.lower()):
                return 'tar.gz'
            else:
                return 'gz'
        elif output.startswith('application/x-bzip2'):
            if common.any_in_string(('.tar.', '.tgz'), file_path.lower()):
                return 'tar.bz2'
            else:
                return 'bz2'
        elif output.startswith('application/zip'):
            return 'zip'
        elif output.startswith('application/x-7z-compressed'):
            return '7zip'
        elif output.startswith('application/x-rar'):
            return 'rar'
    return output.split(';')[0]

def _archive_get_opener(archive_path, file_type=None):
    if file_type == None:
        file_type = get_file_type(archive_path)

    if file_type == 'zip':
        opener, mode = zipfile.ZipFile, 'r'
    elif file_type == 'tar.gz':
        opener, mode = tarfile.open, 'r:gz'
    elif file_type == 'tar.bz2':
        opener, mode = tarfile.open, 'r:bz2'
    else:
        raise (
            TypeError,
            'Unsupported archive type for "{path}": {ftype}'.format(
                path = archive_path,
                ftype = file_type
        ))
    return opener, mode

def archive_list_files(archive, file_type=None, return_objects=False):
    if file_type == None and type(archive) == str:
        file_type = get_file_type(archive)
    elif file_type == None:
        raise ValueError, "If file_type is None, archive needs to be a filename path"

    if type(archive) == str:
        opener, mode = _archive_get_opener(archive)
        archive_file = opener(archive, mode)
    else:
        archive_file = archive
    members = []
    try:
        if file_type.startswith('tar'):
            members = archive_file.getmembers()
            if not return_objects:
                members = [
                    member.name
                    for member in members
                ]
        elif file_type == 'zip':
            members = archive_file.infolist()
            if not return_objects:
                members = [
                    member.filename
                    for member in members
                ]
    except:
        raise (
            TypeError,
            'Something went wrong. Couldn\'t read archive: "{0}"'.format(
                archive_path
        ))
    return members

def archive_extract_file(archive_path, extract_file=None, destination_dir='.'):
    file_type = get_file_type(archive_path)
    if file_type.startswith('tar'):
        type_is_tar = True
    elif file_type == 'zip':
        type_is_tar = False
    else:
        raise TypeError, "Unsupported archive type for \"%s\": %s" % (archive_path, file_type)

    opener, mode = _archive_get_opener(archive_path, file_type)
    archive_file = opener(archive_path, mode)
    file_list = archive_list_files(archive_file, file_type)

    if type_is_tar:
        file_list_to_extract = [
            i for i in file_list
            if (
                i.isfile() and
                fnmatch.fnmatch(i.name.lower(), extract_file)
            )
        ]
    else:
        file_list_to_extract = [
            i for i in file_list
            if (
                i.external_attr != 48 and
                fnmatch.fnmatch(i.filename.lower(), extract_file)
            )
        ]

    if len(file_list_to_extract):
        output_files = []
        if not os.path.isdir(destination_dir):
            try:
                os.mkdir(destination_dir)
            except OSError:
                raise OSError, "Couldn't extract archive \"%s\", does not have write permission in output dir" % archive_path

        for file_info in file_list_to_extract:
            if type_is_tar:
                file_name = file_info.name
                debug("Extracting %s to %s..." % (file_name, destination_dir))
                file_object = archive_file.extractfile(file_info)
                content = file_object.read()
                file_object.close()
            else:
                file_name = file_info.filename
                debug("Extracting %s to %s..." % (file_name, destination_dir))
                content = archive_file.read(file_info)

            output_path = '%s/%s' % (destination_dir, os.path.basename(file_name))
            file_object = open(output_path, 'ab')
            file_object.write(content)
            file_object.close()
            output_files.append(output_path)
    archive_file.close()
    return output_files

def get_modified_time_url(url):
    urlfile = urllib2.urlopen(url)
    headers = urlfile.info()
    return time.strptime(headers['last-modified'], '%a, %d %b %Y %H:%M:%S %Z')

def get_command_output(command, stderr=False, shell=None, dont_parse_command=False):
    process = run_command(command, stderr, shell, dont_parse_command)
    out, err = process.communicate()
    if stderr:
        return out.strip(), err
    else:
        return out.strip()

def run_command(command, stderr=False, shell=None, dont_parse_command=False):
    if not dont_parse_command:
        if type(command) not in [list, tuple, set]:
            command = string_split(command)
        else:
            command = list(command)
    if shell in (True, False):
        process = common.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)
    else:
        process = common.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process


def get_internet_available():
    if len(common.run(['which', 'ip'])[0].strip()):
        # Try testing for IPv4 with the ip command first
        if len(common.run(['ip', '-4', 'route'])[0]):
            return True

    network_manager_tool = common.run(['which', 'nm-tool'])[0].strip()
    if len(network_manager_tool):
        # If Network Manager is available test using that
        info = common.run(network_manager_tool)[0]
        connected = re.search('(?m)^State:\s+(\w+)$', info)
        dns_address = re.search('(?m)^\s*DNS:\s+([\d\.]+)$', info)
        if (
            connected and connected.groups()[0].lower() == 'connected'
        ) and (
            dns_address and len(dns_address.groups()[0].strip())
        ):
            return True
    elif len(common.run(['which', 'ifconfig'])[0].strip()):
        # Else test using the output of ifconfig
        info = common.run(['ifconfig', '-a'])[0]
        for interface in info.split('\n\n'):
            if 'UP BROADCAST RUNNING' in interface and 'inet addr:' in interface:
                return True
    return False

def get_mounted_drives():
    info = common.run('mount')[0]
    drives = []
    for line in filter(len, info.split('\n')):
        line_parts = line.split(' ')

        if len(line_parts) < 6:
            debug('Malformed mount info line: %s' % line)
            continue

        drive = {}
        try:
            drive['options'] = line_parts[-1][1:-1]
            drive['type'] = line_parts[-2]
            drive['dir'] = '/{0}'.format(
                ' /'.join(' '.join(line_parts[0:-3]).split(' /')[1:])
            )
            drive['device'] = ' '.join((
                line.split(drive['dir'])[0]
            ).split(' ')[:-2])
        except:
            print('Malformed mount info line: %s' % line)
            continue

        drives.append(drive)
    return drives

def get_mounted_cds():
    mounted_drives = get_mounted_drives()
    return [
        drive for drive in mounted_drives
        if drive['type'] in ('iso9660', 'udf', 'fuse.fuseiso')
    ]

def dict_to_case_insensitive(dict):
    dict_copy = {}
    for key,value in dict.iteritems():
        if type(key) in (str, unicode):
            dict_copy[key.lower()] = value
        else:
            dict_copy[key] = value
    return dict_copy

def dict_diff(dict_a, dict_b):
    """Returns a dict containing any key that's only in one of the dicts
    and any value that differs in the two dicts.
    In the case of the same key but different value,
    the value from dict_b is returned."""
    return dict([
        (key, dict_b.get(key, dict_a.get(key)))
        for key in set(dict_a.keys()+dict_b.keys())
        if (
            (key in dict_a and (not key in dict_b or dict_a[key] != dict_b[key])) or
            (key in dict_b and (not key in dict_a or dict_a[key] != dict_b[key]))
        )
    ])

def unescape_string(string):
    if len(string):
        chars = [' ', '*', '$', '`', '#']
        if string[0] == '"':
            chars.append("'")
        elif string[0] == "'":
            chars.append('"')
        for char in chars:
            string = string.replace('\\{0}'.format(char), char)
    return string

def string_split(string, remove_escapes=True, retain_defines=False):
    """
    Split a string into a list, by default removing quotation marks around escaped strings
    and optionally leaving definitions (such as PATH="something") unsplit.

    Also, this function doesn't crash on badly formatted substrings and understands sub-substrings."""

    string_parts = [
        i for i in re.split(
            r'((?<!\\)\s+|(?<!\\)".*?(?<!\\)"|(?<!\\)\'.*?(?<!\\)\')', string
        )
    ]

    if retain_defines:
        new_string_parts = []
        i = 0
        while i < len(string_parts):
            if string_parts[i].endswith('='):
                if len(string_parts[i+1].strip()):
                    new_string_parts.append(string_parts[i]+string_parts[i+1])
                    i += 1
                else:
                    new_string_parts.append(string_parts[i])
            elif len(string_parts[i].strip()):
                new_string_parts.append(string_parts[i])
            i += 1
        string_parts = new_string_parts
    else:
        string_parts = [
            i.strip('"').strip("'").strip('\\"').strip("\\'")
            for i in string_parts
        ]

    if remove_escapes:
        string_parts = [
            i[1:-1]
            if (len(i) and i[0] in ('"', "'"))
            else i
            for i in string_parts
        ]
        for char in (' ', '*', '$', '`', '#'):
            string_parts = [
                unescape_string(i)
                for i in string_parts
            ]

    return filter(lambda i: len(i.strip()), string_parts)

def get_program_name(exe):
    """
    Try to read the program name from the executables meta data, else return
    a capitalised version of the filename."""
    collected_names = []

    try:
        version_info = binary.windows_executable(exe).get_version_fast()
        if 'ProductName' in version_info:
            collected_names.append(version_info['ProductName'])
        if 'FileDescription' in version_info:
            collected_names.append(version_info['FileDescription'])
        if 'Comments' in version_info:
            collected_names.append(version_info['Comments'])
    except:
        pass

    manifest = common.run(['wrestool', '--extract', '--raw', '-t24', exe])[0]
    try:
        collected_names.append(
            re.search(
                '<description>([^<]*?)</description>', manifest
            ).groups()[0]
        )
    except AttributeError:
        pass

    names = []
    for name in collected_names:
        if name is not None:
            name = name.strip().replace('\x00','')
            if not any((
                (
                    name.lower().startswith(title) or
                    not len(name)
                ) for title
                in (
                    'microsoft.windows.common-controls',
                    'nullsoft install system',
                    'inno setup',
                    '{cm:InstallName}'
                )
            )):
                names.append(name)

    if len(names):
        # Use longest name
        return sorted(names, key=len)[-1]
    else:
        name = os.path.basename(exe)[:-4].replace('_', ' ')
        if name.lower() == name or name.upper() == name:
            return " ".join([ i.capitalize() for i in name.split() ])
        else:
            return name



def icon_get_path_from_name(name):
    if name is None or not len(name.strip()):
        return None
    if name.startswith('/') and os.path.exists(name):
        return name

    for path in [
        '{home}/.icons'.format(home = common.ENV['HOME']),
        '{prefix}/../.icons'.format(prefix = common.ENV['WINEPREFIX']),
        '{home}/.local/share/icons'.format(home = common.ENV['HOME']),
        '{prefix}/../.local/share/icons'.format(prefix = common.ENV['WINEPREFIX']),
        '/usr/local/share/icons/hicolor',
        '/usr/local/share/icons',
        '/usr/local/share/pixmaps'
        '/usr/share/icons/hicolor',
        '/usr/share/icons',
        '/usr/share/pixmaps'
    ]:
        if os.path.isdir(path):
            for file_name in os.listdir(path):
                if file_name.startswith(name):
                    return os.path.realpath(os.path.join(path, file_name))
        else:
            for file_name in [
                name,
                '{0}.png'.format(name),
                '{0}.xpm'.format(name),
                '{0}.ico'.format(name),
                '{0}.bmp'.format(name),
                '{0}.tga'.format(name),
                '{0}.tif'.format(name),
            ]:
                if os.path.isfile(os.path.join(path, file_name)):
                    return os.path.realpath(os.path.join(path, file_name))
    return None



def get_pids_using_file(file_name):
    pids = common.run(['lsof', '-t', '-f', '--', str(file_name)])[0].strip()
    pids_list = []
    for pid in pids.split():
        try:
            pids_list.append(int(pid.strip()))
        except:
            continue
    return pids_list

def get_pid_from_process_name(name):
    pid = common.run(['pgrep', str(name)])[0].strip()
    try:
        return int(pid)
    except:
        return None

def get_pids_of_pgid(pgid):
    pgid = str(pgid)
    process_list = common.run(['ps', '-U', os.environ['USER'],
                               '-o', 'pgrp=',
                               '-o', 'pid='
    ])[0].split('\n')
    new_list = []
    for info in process_list:
        try:
            pgrp, pid = info.split()
        except:
            continue
        if str(pgrp) == pgid:
            try:
                new_list.append(int(pid))
            except:
                continue
    return new_list

def get_pids_of_user_processes():
    process_list = common.run(['ps', '-U', os.environ['USER'],
                               '-o', 'pid='
    ])[0].split('\n')
    new_list = []
    for pid in process_list:
        try:
            new_list.append(int(pid))
        except:
            pass
    return new_list

def get_cmd_of_pid(pid):
    return common.run(['ps', '-p', '%s' % pid, '-o', 'cmd='])[0].strip()

def get_pgid_of_pid(pid):
    try:
        return int(common.run(['ps', '-p', str(pid), '-o', 'pgid='])[0].strip())
    except ValueError:
        return None

def get_start_time_of_pid(pid):
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

    stime = common.run(['ps', '-p', '%s' % pid, '-o', 'start='])[0].strip()
    # If stime is of the form 'mmm dd'
    if ' ' in stime:
        month = months.index( stime.split(' ')[0].lower() )+1
        day = int(stime.split(' ')[1])
        return (month, day, 0, 0, 0)
    # If stime is of the form 'HH:MM:SS'
    elif ':' in stime:
        hour, minute, second = [ int(i) for i in stime.split(':') ]
        return (0, 0, hour, minute, second)

def get_state_code_of_pid(pid):
    return common.run(['ps', '-p', '%s' % pid, '-o', 's='])[0].strip().upper()


def get_elapsed_time_of_pid(pid):
    """
    Return the elapsed time since the process was started.
    Returns a tuple in the form of (days, hours, minutes, seconds)."""
    etime = common.run(['ps', '-p', '%s' % pid, '-o', 'etime='])[0].strip()
    if len(etime) >= len('dd-hh:mm:ss'):
        days, rest = etime.split('-')
        hours, minutes, seconds = ( int(i) for i in rest.split(':') )
        return int(days), hours, minutes, seconds
    elif len(etime) >= len('hh:mm:ss'):
        hours, minutes, seconds = ( int(i) for i in etime.split(':') )
        return 0, hours, minutes, seconds
    elif len(etime) >= len('mm:ss'):
        minutes, seconds = ( int(i) for i in etime.split(':') )
        return 0, 0, minutes, seconds

def get_elapsed_time_since(seconds):
    if type(seconds) not in (int, float):
        seconds = time.mktime(seconds)

    seconds = time.time() - seconds

    days = int(seconds / 60 / 60 / 24 )
    seconds -= days * 60 * 60 * 24

    hours = int(seconds / 60 / 60)
    seconds -= hours * 60 * 60

    minutes = int(seconds / 60)
    seconds -= minutes * 60

    return (days, hours, minutes, seconds)

def find_uppercase_filenames(path=None):
    # TODO: Needs to not break on recursive symlinks, as this tends to happen
    #       when the user links to his/her home-dir.
    # TODO: Possibly convert to use the yield statement as this takes a while
    #       and a GUI would most likely like to track the progress.
    if path == None:
        path = drives.get_main_drive(use_registry=False)['mapping']
    filelist = []
    filelist_conflicts = []
    visited_paths = []

    for root, dirs, files in os.walk(path, followlinks=True):
        absolute_root = os.path.realpath(root)
        if absolute_root in visited_paths:
            continue

        visited_paths.append(absolute_root)
        for name in files + dirs:
            lowname = name.lower()
            if name != lowname:
                full_name = os.path.join(root, name)
                if os.path.exists(os.path.join(root, lowname)):
                    filelist_conflicts.append(full_name)
                else:
                    filelist.append(full_name)

    return filelist, filelist_conflicts


def file_get_mimetype(filename):
    mimetype = common.run(['file', '-bi', filename])[0]
    try:
        return mimetype.split(';')[0].strip()
    except:
        return "unknown"


def get_mount_iso_path(iso_path):
    """Return path to where the image at iso_path would be mounted"""
    return '{0}/mounted_files/{1}'.format(
        common.ENV['VINEYARDPATH'], iso_path.replace('/', '-')
    )

def mount_iso(iso_path):
    """Mounts the iso file given and returns the path to the mount point or None if the mount failed."""
    if common.which('fuseiso') and (
        os.path.exists(iso_path) and os.access(iso_path, os.R_OK)
    ):
        mount_dir = get_mount_iso_path(iso_path)
        return_output, return_error, return_code = common.run(
            ['fuseiso', '-p', iso_path, mount_dir],
            include_return_code = True
        )
        print(return_output)
        print(return_error)
        if return_code == 0:
            return mount_dir
    return None


def get_real_home():
    # Figure out the real home, if we're in a bottle
    if os.path.normpath(os.path.expandvars("$HOME/..")) == "/home":
        return os.path.expandvars("$HOME")
    else:
        return os.path.normpath(os.path.expandvars("$HOME/../.."))
getRealHome = get_real_home


def get_user_default_shell():
    f = open('/etc/passwd', 'r')
    shell = None
    for i in f.readlines():
        if i.startswith(common.ENV['USER']):
            shell = i
            break
    f.close()
    if shell:
        return shell.split(':')[-1].strip()
    else:
        return "/usr/bin/sh"


"""
    The following functions are based on functions in the xdg-utils package
    (http://webcvs.freedesktop.org/portland/portland/xdg-utils/)
"""
def get_desktop_environment():
    env =  dict((k.lower(), v) for (k, v) in common.ENV.iteritems())
    if 'gnome_desktop_session_id' in env and env['gnome_desktop_session_id'] != "":
        return "gnome"
    elif 'kde_full_session' in env and env['kde_full_session'] == "true":
        return "kde"
    elif subprocess.call("xprop -root _DT_SAVE_MODE | grep ' = \"xfce4\"$'", shell=True) == 0:
        return "xfce"
    else:
        return "unknown"


def get_default_terminal():
    desktop = get_desktop_environment()
    if desktop == "gnome":
        terminal = get_command_output('gconftool-2 --get "/desktop/gnome/applications/terminal/exec"')
        terminal = (terminal, [get_command_output('gconftool-2 --get "/desktop/gnome/applications/terminal/exec_arg"')])
    elif desktop == "kde":
        terminal = get_command_output('kreadconfig --file kdeglobals --group General --key TerminalApplication --default konsole'), ['-e']
    elif desktop == "xfce":
        terminal = 'exo-open', ['--launch', 'TerminalEmulator']
    else:
        terminal = 'xterm', ['-e']
    return terminal


def get_default_terminal_title():
    shell = get_user_default_shell()
    home = get_real_home()
    # We define PS1 in the next line to make the .profile script assume
    # that it is running in an interactive shell
    title = get_command_output((
        "{shell} -c 'PS1=dummy; "+ \
        "if [ -f {home}/.profile ]; "+ \
            "then . {home}/.profile; "+ \
        "fi; "+ \
        "echo $PS1'").format(shell=shell, home=home))
    return title


def run_in_terminal(shellcommand):
    terminal, args = get_default_terminal()
    env = common.ENV.copy()
    env['HOME'] = getRealHome()
    return subprocess.Popen(
        [terminal]+args+[shellcommand],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def open_terminal(cwd=None, configuration_name=None, cmd=None, arguments=[], disable_pulseaudio=False, keep_open=False):
    terminal, args = get_default_terminal()
    shell = get_user_default_shell()

    if cwd == None or not os.path.isdir(cwd):
        # If no (existing) current work dir was given,
        # choose the first virtual drive in the Wine configuration
        cwd = drives.get_main_drive(use_registry=False)['mapping']

    env = common.ENV.copy()
    home = env['HOME'] = getRealHome()

    if configuration_name == None:
        conf_name = prefixes.get_name()
    else:
        conf_name = configuration_name

    shell_args = []
    if conf_name != None:
        start_script_filename = tempname('terminal-script-', '.sh')
        start_script_file = open(start_script_filename, 'w')
        # Writes a shell script that mimics the normal interactive shell
        # behaviour and ends by prepending the Terminal title with the name
        # of the current configuration
        start_script_file.write((
            'PS1=dummy; '+
            'if [ -f /etc/profile ]; then '+
            '  . /etc/profile; '+
            'fi; '+
            'if [ -f {home}/.bash_profile ]; then '+
            '  . {home}/.bash_profile; '+
            'elif [ -f {home}/.bash_login ]; then '+
            '  . {home}/.bash_login; '+
            'elif [ -f {home}/.profile ]; then '+
            '  . {home}/.profile; '+
            'fi; '+
            'PS1=${{PS1/0;/0;{conf}: }}; '+
            'export PS1').format(
                home = env['HOME'],
                conf = conf_name)
        )
        start_script_file.close()
        shell_args = ['--init-file', start_script_filename]

    if len(arguments):
        def _arg_escape(arg):
            shell_chars = (' ', '"', "'", '(', ')', '`', '$', '!')
            if common.any_in_string(shell_chars, arg):
                # return "'{0}'".format(string_escape_char(arg, "'"))
                return "'{0}'".format(arg.replace("'", """'"'"'"""))
            else:
                return arg

        shell_commands = '{0} {1}'.format(
            ('' if cmd == None else cmd),
            ' '.join(
                _arg_escape(arg)
                for arg
                in arguments
            )
        )
        if disable_pulseaudio:
            arguments = ['-c', 'killall pulseaudio; {0}; pulseaudio &'.format(
                shell_commands
            )]
        else:
            if keep_open:
                arguments = ['-c', '{0};echo; echo "{1}";read'.format(
                    shell_commands,
                    _("Press enter to close the terminal.")
                )]
            else:
                arguments = ['-c', '{0}'.format(
                    shell_commands
                )]

    print([terminal]+args+[shell]+shell_args+arguments)
    process = subprocess.Popen(
        [terminal]+args+[shell]+shell_args+arguments,
        cwd=cwd,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process

