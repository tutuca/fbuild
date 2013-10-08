# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui,
#               2013 Gonzalo Bonigo, Gustavo Ojeda, Matias Iturburu,
#                    Leandro Moreno, FuDePAN
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
from distutils.dir_util import mkpath
from SCons.Node.FS import Dir
import fbuild_exceptions


# Constants for the distributions supported.
DISTRO_UBUNTU = 'UBUNTU'
DISRTO_ARCH = 'ARCH'
# Path to the /etc/issue file which contains the distribution.
_DISRTO_FILE = '/etc/issue'
# Path to the process file system.
_PROC_DIR = '/proc/%d'


def FindFiles(env, fromDir, filters=None):
    filters = filters if filters is not None else ['*']
    path = fromDir.abspath
    files = []
    for x in env.Glob(path + '/*'):
        #s.isdir doesn't work as expected in variant dir (when the dir is not created)
        if isinstance(x, Dir):
            files.extend(FindFiles(env, x, filters))
        else:
            if any([fnmatch.fnmatch(x.abspath, filter) for filter in filters]):
                if os.path.isfile(x.abspath.replace('/build/', '/projects/')):
                    files.append(x)
    return files


#
# TODO: Rewrite this method!!!!
# refactor_trials_count = 3
# NOTE: If you do try to refactor this method please update the counter above.
def RecursiveInstall(env, sourceDir, sourcesRel, targetName, fileFilter=None):
    fileFilter = fileFilter if fileFilter is not None else ['*.*']
    nodes = []
    for s in sourcesRel:
        nodes.extend(FindFiles(env, s, fileFilter))
    l = len(sourceDir.abspath) + 1
    relnodes_abspath = []
    relnodes_shrtpath = []
    srcnodes = []
    for n in nodes:
        # Add the path if the sourceDir is in the source path.
        if sourceDir.abspath in n.abspath:
            srcnodes.append(n.abspath[l:])
        # If not, go back one path in the sourceDir and check if now
        # is into the source path.
        else:
            # Take the path after the abspath.
            path = sourceDir.abspath.split(os.path.abspath(''))[1]
            node_path = ''
            for i in range(1, path.count('/')):
                # Remove the last directory in the path.
                path = os.path.dirname(path)
                # Check if the path was added to relnodes before.
                if path in n.abspath and not node_path in relnodes_shrtpath:
                    # remove the first '/'
                    node_path = n.abspath.split(path)[1][1:]
                    relnodes_shrtpath.append(node_path)
                    relnodes_abspath.append(n.abspath)
    targetHeaderDir = env.Dir(env['INSTALL_HEADERS_DIR']).Dir(targetName).abspath
    targets = []
    sources = []
    # if targetName == 'ucpapp': import ipdb; ipdb.set_trace()
    for n in srcnodes:
        t = env.File(os.path.join(targetHeaderDir, n))
        s = sourceDir.File(n)
        targets.append(t)
        sources.append(s)
    for i in range(0, len(relnodes_shrtpath)):
        t = env.File(os.path.join(targetHeaderDir, relnodes_shrtpath[i]))
        s = relnodes_abspath[i]
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
        with open(os.devnull, "w") as fnull:
            stdout = fnull if silent else None
            if silent:
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


def CheckPath(path, create=True):
    if not os.path.exists(path):
        if create:
            mkpath(path)
        return False
    return True


def ProcessExists(pid):
    """
    Checks if the process with PID pid exists.
    """
    return os.path.exists(_PROC_DIR % pid)


def WaitProcessExists(pid):
    """
    Waits until exists a process with PID pid.
    """
    while not ProcessExists(pid):
        pass
