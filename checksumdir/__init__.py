"""
Function for deterministically creating a single hash for a directory of files,
taking into account only file contents and not filenames.

Usage:

from checksumdir import dirhash

dirhash('/path/to/directory', 'md5')

"""

import os
import hashlib
import re

import pkg_resources

__version__ = pkg_resources.require("checksumdir")[0].version

HASH_FUNCS = {
    'md5': hashlib.md5,
    'sha1': hashlib.sha1,
    'sha256': hashlib.sha256,
    'sha512': hashlib.sha512
}

def dirhash(dirname, hashfunc='md5', excluded_files=None, ignore_hidden=False,
            followlinks=False, excluded_extensions=None, datafunc='deep'):
    hash_func = HASH_FUNCS.get(hashfunc)
    data_func = DATA_FUNCS.get(datafunc)
    if not hash_func:
        raise NotImplementedError('{} not implemented.'.format(hashfunc))
    if not data_func:
        raise NotImplementedError('{} not implemented.'.format(datafunc))

    if not excluded_files:
        excluded_files = []

    if not excluded_extensions:
        excluded_extensions = []

    if not os.path.isdir(dirname):
        raise TypeError('{} is not a directory.'.format(dirname))

    hashvalues = []
    for root, dirs, files in os.walk(dirname, topdown=True, followlinks=followlinks):
        if ignore_hidden and re.search(r'/\.', root):
            continue

        for fname in files:
            if ignore_hidden and fname.startswith('.'):
                continue

            if fname.split('.')[-1:][0] in excluded_extensions:
                continue

            if fname in excluded_files:
                continue

            hashvalues.append(data_func(os.path.join(root, fname), hash_func))

    return _reduce_hash(hashvalues, hash_func)

def _stathash(filepath, hashfunc):
    hasher = hashfunc()
    if not os.path.exists(filepath):
        return hasher.hexdigest()

    statinfo = os.stat(filepath)
    hasher.update(filepath.encode('UTF-8'))

    for attr in statinfo:
        hasher.update(str(attr).encode('UTF-8'))
    return hasher.hexdigest()

def _filehash(filepath, hashfunc):
    hasher = hashfunc()
    blocksize = 64 * 1024

    if not os.path.exists(filepath):
        return hasher.hexdigest()

    with open(filepath, 'rb') as fp:
        while True:
            data = fp.read(blocksize)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()

def _reduce_hash(hashlist, hashfunc):
    hasher = hashfunc()
    for hashvalue in sorted(hashlist):
        hasher.update(hashvalue.encode('utf-8'))
    return hasher.hexdigest()

DATA_FUNCS = {
    'shallow': _stathash,
    'deep': _filehash
}


