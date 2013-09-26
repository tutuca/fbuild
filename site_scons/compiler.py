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


"""This file contains all the compiler related stuff."""


import platform

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
