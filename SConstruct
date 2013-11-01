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

import extension_qt
import SCons

env = Environment()

hasQt = extension_qt.HasQt(env)

if hasQt:
    env = Environment(tools=['default', 'qt4'])
    env['QT_PRESENT'] = hasQt
    env['QT4_DEBUG'] = 1

Export('env')

vars = Variables('SConfig')
Export('vars')

# Set command line arguments.
import options
options.init(env)

# Color pretty printing
import termcolor
termcolor.init(env)

# Default configuration options
import scons_defaults
scons_defaults.init(env, vars)

# Imports compiler stuff
import compiler
compiler.init(env)

# Linker options
import linker
linker.init(env)

# Include the aliases helper
import helpfromaliases
helpfromaliases.init(env)

# Include the builders
import builders
builders.init(env)

# Include the dependencies checkout and update system
import dependencies
dependencies.init(env)

# Include the graph dependency solver
import dependencygraph
dependencygraph.init(env)

# Add OS Components
import os_specifics_linux
os_specifics_linux.init(env)

# Add Qt
if hasQt:
    extension_qt.init(env)

import fudepan
fudepan.SetDefines(env)

## Walk over the tree finding components
dependencygraph.WalkDirsForSconscripts(env)
