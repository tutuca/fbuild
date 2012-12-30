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
# Description: linux specific modules
#

def init(env):
    for module in ['pthread', 'dl', 'gcov']:
        env.CreateExternalLibraryComponent(module, [], env.Dir('/usr/lib'), [], True)
