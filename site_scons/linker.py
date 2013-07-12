# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011 Esteban Papp, Hugo Arregui, 2013 Gonzalo Bonigo, FuDePAN
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
    This file contains linker options and settings.
"""


import platform


def init(env):
    (arch, binType) = platform.architecture()
    if binType == 'ELF':
        LinuxOptions(env)


def LinuxOptions(env):
    # Resolve the rpath so everything works smooth from
    # the install dir. This makes easier to deploy somewhere
    # else, you only need to pass INSTALL_<BIN/LIB/HEADERS>_DIR parameters to
    # scons to deploy it somewhere else.
    #env.Append(RPATH=env['INSTALL_LIB_DIR'])
    #env['ENV']['LD_LIBRARY_PATH'] = env['INSTALL_LIB_DIR']
    pass
