# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2013 Gonzalo Bonigo, Gustavo Ojeda, FuDePAN
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
    This file allows to add command line flag for fbuild.
"""

from SCons.Script import AddOption

def init(env):
    AddOption(
        '--jenkins',
        dest='jenkins',
        action='store_true',
        help='Switch the run mode to jenkins.',
        default=False
    )
    AddOption(
        '--verbose',
        dest='verbose',
        action='store_false',
        help='Display a more detailed output.',
        default=True
    )
    AddOption(
        '--mocko',
        dest='verbose',
        action='store_false',
        help='Run the tests using mocko.',
        default=True
    )
