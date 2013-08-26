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
import sys
import os

from SCons.Node.FS import Dir
import fbuild_exceptions


# Contants for the distributions supported.
DISTRO_UBUNTU = 'UBUNTU'
DISRTO_ARCH = 'ARCH'
# Path to the /etc/issue file which contains the distro.
_DISRTO_FILE = '/etc/issue'


def FindFiles(env, fromDir, filters=None):
    filters = filters if filters is not None else ['*']
    path = fromDir.abspath
    files = []
    for s in env.Glob(path + '/*'):
        #s.isdir doesn't work as expected in variant dir (when the dir is not created)
        if isinstance(s, Dir):
            files.extend(FindFiles(env, s, filters))
        else:
            if any([fnmatch.fnmatch(s.abspath, filter) for filter in filters]):
                if os.path.isfile(s.abspath.replace('/build/', '/projects/')):
                    files.append(s)
    return files


#
# TODO: Rewrite this method!!!!
#
def RecursiveInstall(env, sourceDir, sourcesRel, targetName, fileFilter=None):
    fileFilter = fileFilter if fileFilter is not None else ['*.*']
    nodes = []
    for s in sourcesRel:
        nodes.extend(FindFiles(env, s, fileFilter))
    l = len(sourceDir.abspath) + 1
    relnodes = [n.abspath[l:] for n in nodes]
    targetHeaderDir = env.Dir(env['INSTALL_HEADERS_DIR']).Dir(targetName).abspath
    targets = []
    sources = []
    for n in relnodes:
        t = env.File(os.path.join(targetHeaderDir, n))
        s = sourceDir.File(n)
        targets.append(t)
        sources.append(s)
    iAs = env.InstallAs(targets, sources)
    return iAs


def RemoveDuplicates(seq, idfun=None): 
    ''''
    Removes duplicates in seq, preserving it's order.
    Uses cmp() so it supports unhashable objects.
    :idfun: is an optional transformation function so we can do this:

        >>> a=list('ABeeE')
        >>> f5(a)
        ['A','B','e','E']
        >>> f5(a, lambda x: x.lower())
        ['A','B','e'] 

    '''
    if idfun is None:
       idfun = lambda x: x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker not in seen:
            seen[marker] = 1
            result.append(item)
    return result


def FilesFlatten(env, path, fileFilter):
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


def DirsFlatten(env, path):
    out = []
    for root, dirnames, filenames in os.walk(path):
        out.append(env.Dir(os.path.join(root, dirnames)))
    return out


def ChainCalls(env, cmds, silent=True):
    if cmds:
        cmd = cmds[0]
        if not silent:
            print '>>', cmd
        #errors always shows
        cmd_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        cmd_proc.stdout.read()
        if cmd_proc.wait():
            env.cerror('error executing: %s' % cmd)
            return cmd_proc.wait()
        else:
            return ChainCalls(env, cmds[1:], silent)
    else:
        return 0


def GetDistro():
    """
        Description:
            This function tells in which distribution of linux we are.
        Arguments:
            None.
        Exceptions:
            DistroError.
        Return:
            A string instance with the name of the distribution.
    """
    try:
        f = open(_DISRTO_FILE, 'r')
    except OSError:
        raise fbuild_exceptions.DistroError()
    else:
        result = None
        distro = (f.readline().split())[0]
        f.close()
        if distro in ['Ubuntu', 'ubuntu', 'UBUNTU']:
            result = DISTRO_UBUNTU
        elif distro in ['Arch', 'arch', 'ARCH']:
            result = DISRTO_ARCH
        else:
            raise fbuild_exceptions.DistroError()
        return result


def WasTargetInvoked(target):
    """
        Description:
            This function tells if a specific target was invoked or not.
        Arguments:
            target  -  A string instance with the name of target to be check.
        Exceptions:
            None.
        Return:
            True  if the target was called.
            False otherwise.
    """
    for arg in sys.argv:
        if arg == target:
            return True
    return False


def FindSources(dirs, extensions, spacer=' '):
    out = []
    
    for source in dirs:
        name, ext = os.path.splitext(source.name)
        if ext in extensions:
            out.append(source.abspath)
    
    return ' '.join(out)

def FindHeaders(dirs):
    out = []
    for source in dirs:
        name, ext = os.path.splitext(source.name)
        if ext in ['.h', '.hh', '.hpp']:
            dirname = os.path.dirname(source.abspath)
            if dirname not in out:
                out.append(dirname)
    return ''.join('-I%s ' %x for x in out)
