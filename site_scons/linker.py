# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Esteban Papp, Hugo Arregui, FuDePAN
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


def init(env):
    import platform
    (arch,binType) = platform.architecture()
    if binType == 'ELF':
        linuxOptions(env)

def linuxOptions(env):
    # Resolve the rpath so everything works smooth from
    # the install dir. This makes easier to deploy somewhere
    # else, you only need to pass INSTALL_<BIN/LIB/HEADERS>_DIR parameters to 
    # scons to deploy it somewhere else
    #env.Append( RPATH = env['INSTALL_HEADERS_DIR'])
    env.Append( RPATH = env['INSTALL_LIB_DIR'])
    env['ENV']['LD_LIBRARY_PATH'] = env['INSTALL_LIB_DIR'] 

