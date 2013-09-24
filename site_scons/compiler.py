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


"""This file contains all the compiler related stuff."""


import platform
import os
import sys
import subprocess
from SCons.Script import AddOption


def init(env):
    AddOption('--type',
              dest='type',
              type='string',
              nargs=1,
              action='store',
              help='type of build, options: release, opt')
    (arch, binType) = platform.architecture()
    if binType == 'ELF':
        LinuxOptions(env)
        AddNameCheck(env)
        env['SPAWN']=ManageOutput


def LinuxOptions(env):
    AddOption('--effective',
              dest='effective',
              action='store_true',
              help='Sets the effective C++ mode',
              default=False)
    # Common options.
    commonFlags = ['-Wall', '-Wextra', '-pedantic', '-ansi']
    env.Append(CXXFLAGS=commonFlags, CFLAGS=commonFlags)
    # Options for 64bit archs
    (arch, binType) = platform.architecture()
    if arch == '64bit':
        env.Append(CXXFLAGS='-fPIC', CFLAGS='-fPIC')
    # Build type options
    if env.GetOption('type') == 'opt':
        optFlags = ['-O3']
        env.Append(CXXFLAGS=optFlags, CFLAGS=optFlags)
        env.Append(CPPDEFINES=['NDEBUG'])
    elif env.GetOption('type') != 'release':
        dbgFlags = ['-ggdb3']
        env.Append(CXXFLAGS=dbgFlags, CFLAGS=dbgFlags)
        env.Append(CPPDEFINES=['DEBUG'])

def ManageOutput(sh, escape, cmd, args, env):
    # import ipdb; ipdb.set_trace()
    """Spawn which echos stdout/stderr from the child."""
    # convert env from unicode strings
    asciienv = {}
    for key, value in env.iteritems():
        asciienv[key] = str(value)    
        
    p = subprocess.Popen(
        ' '.join(args), 
        env=asciienv, 
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True,
        universal_newlines=True)
    (stdout, stderr) = p.communicate()

    # Does this screw up the relative order of the two?
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    return p.returncode

def AddNameCheck(env):
    namecheck = os.path.join(os.getcwd(), "install", "libs", "libnamecheck.so")
    namecheck_conf = os.path.join(os.getcwd(), "conf", "namecheck-conf.csv")
    if os.path.exists(namecheck) and os.path.exists(namecheck_conf):
        plugin = '-fplugin=%s' % namecheck
        conf = '-fplugin-arg-libnamecheck-path=%s' % namecheck_conf
        env.Append(CXXFLAGS=[plugin,conf], CFLAGS=[plugin, conf])
