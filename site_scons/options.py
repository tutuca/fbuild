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
    This file allows to add command line flag for fbuild.
"""


from SCons.Script import AddOption


def init(env):
    AddOption(
        '--verbose',
        dest='verbose',
        action='store_true',
        help='Display a more detailed output.',
        default=False
    )
    AddOption(
        '--buildtests',
        dest='buildtests',
        action='store_true',
        help='''this flag is used to test the build environment, it will parse 
                the buildtests folder instead of the projects folder''',
        default=False)
    AddOption(
        '--forcerun',
        dest='forcerun',
        action='store_true',
        help='''if indicated, tests will run regardless something they depend 
                on changed, if not indicated, tests will only run if something that they depend on changed''',
        default=False)
    AddOption(
        '--nostdin',
        dest='nostdin',
        action='store_true',
        help='''this flag is used to avoid the environment to use stdin to ask 
                stuff, it should assume the default behavior (added to support Eclipse plugin)''',
        default=False)

    if env.GetOption('buildtests'):
        env['WS_DIR'] = env.Dir('#/buildtests').abspath