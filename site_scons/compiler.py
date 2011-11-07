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

import platform

def loadLinuxCompilerOptions(env):
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
		env.Append(CXXFLAGS = dbgFlags, CFLAGS = dbgFlags)
		env.Append(CPPDEFINES = ['DEBUG'])
	elif env.GetOption('type') == 'opt':
		optFlags = [
			'-O3'
		]
		env.Append(CXXFLAGS = optFlags, CFLAGS = optFlags)
		env.Append(CPPDEFINES = ['NDEBUG'])
	if env.GetOption('effective'):
		env.Append(CXXFLAGS = '-Weffc++', CFLAGS = '-Weffc++')
	if env.GetOption('gprofile'):
		env.Append(CXXFLAGS = '-pg', CFLAGS = '-pg')
	if env.GetOption('gcoverage'):
		gprofFlags = [
				'-fprofile-arcs',
				'-ftest-coverage'
			]
		env.Append(CXXFLAGS = gprofFlags, CFLAGS = gprofFlags)

def loadCompilerOptions(env):
    (arch,binType) = platform.architecture()
    if binType == 'ELF':
        loadLinuxCompilerOptions(env)

    

