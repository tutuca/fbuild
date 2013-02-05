# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Esteban Papp, FuDePAN
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

#
# Description: this file contains all the compiler related stuff
#

import platform
from SCons.Script import AddOption

def init(env):
    AddOption('--type',
              dest='type',
              type='string',
              nargs=1,
              action='store',
              help='type of build, options: dbg (default), opt',
              default='dbg')
    (arch,binType) = platform.architecture()
    if binType == 'ELF':
        linuxOptions(env)

def linuxOptions(env):
    AddOption('--effective',
              dest='effective',
              action='store_true',
              help='Sets the effective C++ mode',
              default=False)
#    AddOption('--gprofile',
#              dest='gprofile',
#              action='store_true',
#              help='Sets the -pg flag to enable gprof',
#              default=False)
    AddOption('--gcoverage',
              dest='gcoverage',
              action='store_true',
              help='Sets the required flags to enable gcov',
              default=False)

    # common options
    commonFlags = [
        '-Wall',
        '-Wextra',
        '-pedantic',
        '-ansi'
    ]
    env.Append(CXXFLAGS = commonFlags, CFLAGS = commonFlags)
    
    # Options for 64bit archs
    (arch,binType) = platform.architecture()
    if arch == '64bit':
        env.Append(CXXFLAGS = '-fPIC', CFLAGS = '-fPIC')
    # build type options
    if env.GetOption('type') == 'dbg':
        dbgFlags = [
            '-ggdb3'
            ]
        env.Append(CXXFLAGS=dbgFlags, CFLAGS=dbgFlags)
        env.Append(CPPDEFINES=['DEBUG'])
    elif env.GetOption('type') == 'opt':
        optFlags = [
            '-O3'
        ]
        env.Append(CXXFLAGS=optFlags, CFLAGS=optFlags)
        env.Append(CPPDEFINES=['NDEBUG'])
#    if env.GetOption('effective'):
#        env.Append(CXXFLAGS='-Weffc++', CFLAGS='-Weffc++')
#    if env.GetOption('gprofile'):
#        env.Append(CXXFLAGS='-pg', CFLAGS='-pg')
    if env.GetOption('gcoverage'):
        gprofFlags = [
                '--coverage'
            ]
        env.Append(CXXFLAGS=gprofFlags, CFLAGS=gprofFlags, LINKFLAGS=gprofFlags)
