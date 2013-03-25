# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Esteban Papp, 2013 Gonzalo Bonigo, FuDePAN
# 
# This file is part of the fudepan-build build system.
# 
# fudepan-build is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# fudepan-build is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with fudepan-build.  If not, see <http://www.gnu.org/licenses/>.


"""
    This module contains utile functions for fbuild.
"""


import subprocess
import fnmatch
import os

from SCons.Node.FS import Dir


# Contants for the distributions supported.
DISTRO_UBUNTU = 'UBUNTU'
DISRTO_ARSH = 'ARCH'
# Path to the /etc/issue file which contains the distro.
_DISRTO_FILE = '/etc/issue'


class DistroError (Exception):
    """
        This class exception is used by the function get_distro().
    """
    pass


def findFiles(env, fromDir, filters=None):
    if filters == None:
        filters = ['*']
    path = fromDir.abspath
    files = []
    for s in env.Glob(path + '/*'):
        if isinstance(s, Dir): #s.isdir doesn't work as expected in variant dir (when the dir is not created)
            files.extend(findFiles(env, s, filters))
        else:
            if any([fnmatch.fnmatch(s.abspath, filter) for filter in filters]):
                files.append(s)
    return files


def RecursiveInstall(env, sourceDir, sourcesRel, targetName, fileFilter=None):
    if fileFilter == None:
        fileFilter = ['*.*']
    nodes = []
    for s in sourcesRel:
        nodes.extend(findFiles(env, s, fileFilter))
    l = len(sourceDir.abspath) + 1
    relnodes = [ n.abspath[l:] for n in nodes ]
    targetHeaderDir = env.Dir(env['INSTALL_HEADERS_DIR']).Dir(targetName).abspath
    targets = []
    sources = []
    for n in relnodes:
        t = env.File(os.path.join(targetHeaderDir, n))
        s = sourceDir.File(n)
        targets.append( t )
        sources.append( s )
    iAs = env.InstallAs(targets, sources)
    return iAs


## {{{ http://code.activestate.com/recipes/52560/ (r1)
def removeDuplicates(s):
    """Return a list of the elements in s, but without duplicates.

    For example, unique([1,2,3,1,2,3]) is some permutation of [1,2,3],
    unique("abcabc") some permutation of ["a", "b", "c"], and
    unique(([1, 2], [2, 3], [1, 2])) some permutation of
    [[2, 3], [1, 2]].

    For best speed, all sequence elements should be hashable.  Then
    unique() will usually work in linear time.

    If not possible, the sequence elements should enjoy a total
    ordering, and if list(s).sort() doesn't raise TypeError it's
    assumed that they do enjoy a total ordering.  Then unique() will
    usually work in O(N*log2(N)) time.

    If that's not possible either, the sequence elements must support
    equality-testing.  Then unique() will usually work in quadratic
    time.
    """
    n = len(s)
    if n == 0:
        return []
    # Try using a dict first, as that's the fastest and will usually
    # work.  If it doesn't work, it will usually fail quickly, so it
    # usually doesn't cost much to *try* it.  It requires that all the
    # sequence elements be hashable, and support equality comparison.
    u = {}
    try:
        for x in s:
            u[x] = 1
    except TypeError:
        del u  # move on to the next method
    else:
        return u.keys()
    # We can't hash all the elements.  Second fastest is to sort,
    # which brings the equal elements together; then duplicates are
    # easy to weed out in a single pass.
    # NOTE:  Python's list.sort() was designed to be efficient in the
    # presence of many duplicate elements.  This isn't true of all
    # sort functions in all languages or libraries, so this approach
    # is more effective in Python than it may be elsewhere.
    try:
        t = list(s)
        t.sort()
    except TypeError:
        del t  # move on to the next method
    else:
        assert n > 0
        last = t[0]
        lasti = i = 1
        while i < n:
            if t[i] != last:
                t[lasti] = last = t[i]
                lasti += 1
            i += 1
        return t[:lasti]
    # Brute force is all that's left.
    u = []
    for x in s:
        if x not in u:
            u.append(x)
    return u
## end of http://code.activestate.com/recipes/52560/ }}}


def files_flatten(env, path, fileFilter):
    out = []
    if isinstance(fileFilter, list or tuple):
        for ff in fileFilter:
            for root, dirnames, filenames in os.walk(path):
                for filename in fnmatch.filter(filenames, ff):
                    out.append(env.File(os.path.join(root, filename)))
    else:
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, fileFilter):
                out.append(env.File(os.path.join(root, filename)))
    return out


def dirs_flatten(env, path):
    out = []
    for root, dirnames, filenames in os.walk(path):
        out.append(env.Dir(os.path.join(root, dirnames)))
    return out


def chain_calls(env, cmds, silent=True):
    if cmds:
        cmd = cmds[0]
        with open(os.devnull, "w") as fnull:
            stdout = fnull if silent else None
            rc = subprocess.call(cmd, stdout=stdout, shell=True) #errors always shows
        if rc:
            env.cerror('error executing: %s' % cmd)
            return rc
        else:
            return chain_calls(env, cmds[1:], silent)
    else:
        return 0


def get_distro ():
    try:
        f = open(_DISRTO_FILE, 'r')
    except OSError:
        raise DistroError()
    else:
        result = None
        distro = (f.readline().split())[0]
        f.close()
        if distro in ['Ubuntu', 'ubuntu', 'UBUNTU']:
            result = DISTRO_UBUNTU
        elif distro in ['Arch','arch','ARCH']:
            result = DISRTO_ARSH
        else:
            raise DistroError()
        return result
